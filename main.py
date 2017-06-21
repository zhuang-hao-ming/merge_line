# -*- encoding: utf-8 -*-
from osgeo import ogr
import os

import argparse
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

    # 命令行配置
    parser = argparse.ArgumentParser(description='merge line')
    parser.add_argument('-i', '--input', type=str, help='the path of the input file',  default='./line/line.shp')
    parser.add_argument('-o', '--output', type=str, help='the path of the output file',  default='out_shp0620.shp')
    args = parser.parse_args()


    # 输入文件读取
    in_driver = ogr.GetDriverByName('ESRI Shapefile')
    in_data_set = in_driver.Open(args.input, 1)
    in_layer = in_data_set.GetLayer()
    in_srs = in_layer.GetSpatialRef()

        
    # 输出文件创建
    out_shp = args.output
    out_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(out_shp):
        out_driver.DeleteDataSource(out_shp)
    out_data_set = out_driver.CreateDataSource(out_shp)
    out_layer = out_data_set.CreateLayer('new', in_srs, in_layer.GetGeomType())
    out_layer_defn = out_layer.GetLayerDefn()
    in_layer_defn = in_layer.GetLayerDefn()
    for i in range(0, in_layer_defn.GetFieldCount()):
        field_defn = in_layer_defn.GetFieldDefn(i)        
        out_layer.CreateField(field_defn)
    

    # 以坐标值作为键，点作为值构建字典 
    #
    coordinate_to_point_dict = {}    



    for fea in in_layer:
        geo = fea.GetGeometryRef()
        start_id = fea.GetFieldAsInteger('start_id')
        end_id = fea.GetFieldAsInteger('end_id')
        

        
        for idx,(x,y) in enumerate([geo.GetPoints()[0] , geo.GetPoints()[-1]]):
            
            point = {
                'x': x,
                'y': y,
                'id': fea.GetFID()
            }
            if idx == 0:
                point['start_id'] = start_id                
            elif idx == 1:
                point['end_id'] = end_id
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
    
    
    
    #  
    # 对于分好的组进行merge操作
    #
    for fid_pair_group in fid_pair_groups:
        fids = [item for sublist in fid_pair_group for item in sublist] # 取出组中所有的线id
        fids = list(set(fids)) # 去重
                        

        points_arr = [] # 取出每条线对应的points
        for fid in fids:
            fea = in_layer.GetFeature(fid)
            geom = fea.GetGeometryRef()
            points_arr.append(geom.GetPoints())
        
        
        
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
        
        line = ogr.Geometry(ogr.wkbLineString) # 新建一个线几何体
        

        start_id = coordinate_to_point_dict[str(new_points[0][0]) + ',' + str(new_points[0][1])][0]['start_id']
        end_id = coordinate_to_point_dict[str(new_points[-1][0]) + ',' + str(new_points[-1][1])][0]['end_id']
        
        for points in new_points:
            line.AddPoint(*points)
        fea = in_layer.GetFeature(fids[0]) # TODO 属性表需要merge吗？
        fea.SetField('start_id', start_id)
        fea.SetField('end_id', end_id)
        fea.SetGeometry(line)
        out_layer.CreateFeature(fea)
        print('merge {0} success'.format(fids))

    
    # 输出其它不需要merge的线
    in_layer.ResetReading()
    for fea in in_layer:
        id = fea.GetFID()
        if id not in fid_in_need_merge:
            out_layer.CreateFeature(fea)

        
    out_data_set = None

    print('done!')
            




if __name__ == '__main__':
    #main()
    from timeit import Timer
    t1 = Timer('main()', 'from __main__ import main')
    print(t1.timeit(1))