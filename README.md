## 需求描述

交通路网数据中常常会出现，一条完整的道路在非转向的点，被分裂成了两段。这导致了后续分析的困难（如导航时需要做不必要的转向判断）。这个脚本希望合并那些在非转向点处被分裂成多段的POLYLINE。

如下图所示：
![合并前](https://github.com/zhuang-hao-ming/merge_line/blob/master/screenshot/%E7%A4%BA%E6%84%8F%E8%A6%81%E5%90%88%E5%B9%B6%E7%9A%84%E7%82%B9.jpg)

3，4，5，6号线段和0，1号线段是需求所要合并的线段。7，8，9，10号线段的连接点是有意义的转向点所有不需要合并。

## 技术栈

语言： python
模块： osgeo.ogr(main.py)或者arcpy(main_arc.py)

## 方法

1. 建立字典数据结构，对所有POLYLINE的起点和终点以坐标值作为键进行分组(两个相连的POLYLINE起点和终点的坐标值相同)。
2. 对于1建立的字典，如果一个键对应的POLYLINE数目恰为2，那么这两个POLYLINE是需要合并的线对，建立一个列表记录这些线对
3. 对于2确定的需要合并的线对，继续将多个需要合并在一起的线对分为同一组，建立一个列表记录这些组。
这里使用一个递归的方法来分组：
  1. 首先从2列表中取出一个线对加入组中，然后从2列表中找出和当前线对中的任意一条线相连的线对，如果找到，对于新找到的线对应用相同的方法，继续找到相连的线对，否则停止。
  2. 然后判断2列表是否为空，否则从2列表中取出一个线对加入新的组中，重复上述操作，直到2列表为空。
4. 对于3得到的分组进行merge，合并的方法如下：
  1. 从分组中任意选一条线作为基准，然后必然可以从分组中找到一条线要么和基准的头部相连要么和基准的尾部相连，连接得到新的基准
  2. 重复步骤1，直到分组中的所有线合并完毕


## 使用
```
python main.py -i ./line/line.shp -o ./out.shp
或
python main_arc.py -i ./line/line.shp -o ./out.shp
```

```
usage: main.py [-h] [-i INPUT] [-o OUTPUT]

merge line

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        the path of the input file
  -o OUTPUT, --output OUTPUT
                        the path of the output file

```

注意，路径应该包含目录。输入路径必须存在，输出路径必须不存在。

## 屏幕截图

合并前：

![合并前](https://github.com/zhuang-hao-ming/merge_line/blob/master/screenshot/%E7%A4%BA%E6%84%8F%E8%A6%81%E5%90%88%E5%B9%B6%E7%9A%84%E7%82%B9.jpg)

方框圈出的点的两侧线段需要被合并。

合并后：

![合并后](https://github.com/zhuang-hao-ming/merge_line/blob/master/screenshot/%E5%90%88%E5%B9%B6%E7%BB%93%E6%9E%9C.jpg)

0号线段是原3，4，5，6线段合并的结果
1号线段是原0，1号线段合并的结果

备注： 在一个11个POLYLINE合并到7个POLYLINE的测试数据集中，osgeo.ogr所耗费的时间0.015s,arcpy耗费的时间是2.76秒。大致猜测原因是因为，osgeo.ogr将数据读入内存中操作，arcpy则是在文件中操作，所以在小数据上osgeo.ogr的速度快很多。可以猜想，arcpy有处理超大数据集的能力，而osgeo.ogr则不一定。