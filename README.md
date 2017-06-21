## 需求描述

交通路网数据中常常会出现，一条完整的道路在非转向的点，被分裂成了两段。这导致了后续分析的困难（如导航时需要做不必要的转向判断）。这个脚本希望合并那些在非转向点处被分裂成多段的POLYLINE。

## 技术栈

语言： python
模块： osgeo.ogr(main.py)或者arcpy(main_arc.py)二选一

备注： 在一个11个POLYLINE合并到7个POLYLINE的测试数据集中，osgeo.ogr所耗费的时间0.015s,arcpy耗费的时间是2.76秒。大致猜测原因是因为，osgeo.ogr将数据读入内存中操作，arcpy则是在文件中操作，所以在小数据上osgeo.ogr的速度快很多。可以猜想，arcpy有处理超大数据集的能力，而osgeo.ogr则不一定。


## 思路

1. 获取POLYLINE的起点和终点
2. 以点的坐标为key点为val构建字典
3. len(val) == 2对应的线需要被合并
4. 对于3得到的需要合并的线对，可能存在多个线对需要合并的情况，继续分组，将所有需要合并在一起的线分入一组
5. 合并

备注： 具体见代码


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