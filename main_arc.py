# -*- encoding: utf-8

import arcpy
import argparse
import sys
import os



#
# @param id 线fid
# @param pairs 线对列表
# 从线对列表中找到包含id指定的线的线对，然后从列表中删除它，并返回它
# 如果没有找到，则返回None
#
def find_and_remove_from_pairs(id, pairs):
    for i in range(len(pairs)):
        if id in pairs[i]:
            a = pairs[i]
            pairs.remove(pairs[i])
            return a
    return None


def main():


    # # 命令行配置
    # parser = argparse.ArgumentParser(description='merge line')
    # parser.add_argument('-i', '--input', type=str, help='the path of the input file',  default='./line/line.shp')
    # parser.add_argument('-o', '--output', type=str, help='the path of the output file',  default='./out_shp0621.shp')
    # args = parser.parse_args()

    # # 输入文件必须存在，输出文件必须不存在
    # if not os.path.exists(input_file):
    #     print('the input path does not exist')
    #     sys.exit()
    # if os.path.exists(output_file):
    #     print('the output path does exist')
    #     sys.exit()
    
    
    input_file =  u'./shp/line2.shp'
    output_file = u'./out1.shp'
    
    

    startid_name = 'startid'
    endid_name = 'endid'



    coordinate_to_point_dict = {}    

    with arcpy.da.SearchCursor(input_file, ['OID@', 'SHAPE@', startid_name, endid_name]) as cursor:
        for row in cursor:  

            #—— 获得线上的所有点
            points = []
            for part in row[1]:
                for pnt in part:
                    if pnt:
                        points.append((pnt.X, pnt.Y))                    
                    else:
                        print('interiror ring')
                        sys.exit()
            #————
                
            
            for idx,(x,y) in enumerate([points[0] , points[-1]]):            
                point = {
                    'x': x,
                    'y': y,
                    'id': row[0]
                }
                if idx == 0:
                    point[startid_name] = row[2]                
                elif idx == 1:
                    point[endid_name] = row[3]
                key = str(point['x']) + ',' + str(point['y'])
                if key not in coordinate_to_point_dict:
                    coordinate_to_point_dict[key] = [point]
                else:
                    coordinate_to_point_dict[key].append(point)

    # 需要merge的线对
    fid_pair_need_merge = []
    # 需要merge的线
    fid_in_need_merge = []
    #
    # 如果恰有两个点的坐标值相同，那么这两个坐标点对应的线需要被merge
    #
    for key,val in coordinate_to_point_dict.items():
        if len(val) == 2:
            ids = []
            for point in val:
                fid_in_need_merge.append(point['id'])
                ids.append(point['id'])
            fid_pair_need_merge.append(ids)




    # 多个线对可能需要被merge在一起
    # 进一步把需要被merge在一起的线对分组
    #
    fid_pair_groups = []
    while len(fid_pair_need_merge) > 0:
        fid_pair = fid_pair_need_merge[0]
        a_group = [fid_pair]
        fid_pair_need_merge.remove(fid_pair)

        def inner(ids):            
            id1 = ids[0]
            id2 = ids[1]
            new_ids1 = find_and_remove_from_pairs(id1, fid_pair_need_merge)
            if new_ids1:
                a_group.append(new_ids1)
                inner(new_ids1)
            new_ids2 = find_and_remove_from_pairs(id2, fid_pair_need_merge)
            if new_ids2:
                a_group.append(new_ids2)
                inner(new_ids2)
                    
        
        inner(fid_pair)
        fid_pair_groups.append(a_group)

    print('there are {0} groups needed to be merged'.format(len(fid_pair_groups)))

    # 新建新的shp
    out_shp = output_file
    arcpy.CreateFeatureclass_management(out_path=os.path.dirname(out_shp), out_name=os.path.basename(out_shp), geometry_type='POLYLINE', template=input_file,has_m='DISABLED', has_z='DISABLED', spatial_reference=input_file)

    # 
    insert_cursor = arcpy.da.InsertCursor(out_shp, ['SHAPE@', startid_name, endid_name])


    #  
    # 对于分好的组进行merge操作
    #
    for fid_pair_group in fid_pair_groups:
        fids = [item for sublist in fid_pair_group for item in sublist] # 取出组中所有的线id
        fids = list(set(fids)) # 去重
                        

        points_arr = [] # 取出每条线对应的points

        #——————查找对应fid的线的所有点
        for fid in fids:
            with arcpy.da.SearchCursor(input_file, ['SHAPE@'], '"FID"={0}'.format(fid)) as cursor: # 
                for row in cursor:            
                    points = []
                    for part in row[0]:
                        for pnt in part:
                            if pnt:
                                points.append((pnt.X, pnt.Y))                    
                            else:
                                print('interiror ring')
                                sys.exit()                
                    points_arr.append(points)
        #________
        
        
        new_points = [] # merge后的points

        a_points = points_arr[0] # 任意取一条线作为基准
        points_arr.remove(a_points)                        
        new_points += a_points

        while len(points_arr) > 0:
                                                                                    
            for points in points_arr: # 对于所有剩下的线，一定存在一条线，和当前merge的结果，要么头尾相接，要么尾头相接。
                if new_points[-1] == points[0]:                                        
                    new_points = new_points[0:-1] + points                    
                    points_arr.remove(points)
                    break
                elif new_points[0] == points[-1]: 
                    new_points = points[0:-1] + new_points                
                    points_arr.remove(points)
                    break
                else:
                    continue
        
        
        

        start_id = coordinate_to_point_dict[str(new_points[0][0]) + ',' + str(new_points[0][1])][0][startid_name]
        end_id = coordinate_to_point_dict[str(new_points[-1][0]) + ',' + str(new_points[-1][1])][0][endid_name]
        
        arcpy_points = [arcpy.Point(*points) for points in new_points]

        line = arcpy.Polyline(arcpy.Array(arcpy_points))
        
        insert_cursor.insertRow([line, start_id, end_id])

            
        print('merge {0} success'.format(fids))

    # 输出其它不需要merge的线
    with arcpy.da.SearchCursor(input_file, ['OID@', 'SHAPE@', startid_name, endid_name]) as cursor:
        for row in cursor:
            id = row[0]
            if id not in fid_in_need_merge:
                insert_cursor.insertRow(row[1:])

    print('done!')








    del insert_cursor

if __name__ == '__main__':
    main()
    # from timeit import Timer
    # t1 = Timer('main()', 'from __main__ import main')
    # print(t1.timeit(1))
    

