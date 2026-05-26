import ezdxf

def split_layers_to_dxf(input_dxf_path):
    # 加载DXF文档
    try:
        doc = ezdxf.readfile(input_dxf_path)
    except IOError:
        print(f'Not a DXF file or a generic I/O error.')
        return
    except ezdxf.DXFStructureError:
        print(f'Invalid or corrupted DXF file.')
        return

    msp = doc.modelspace()

    # 遍历所有图层
    for layer in doc.layers:
        layer_name = layer.dxf.name
        print(f"Processing layer: {layer_name}")

        # 创建一个新的DXF文档用于存储单个图层的内容
        new_doc = ezdxf.new(dxfversion=doc.dxfversion)
        new_msp = new_doc.modelspace()

        # 复制属于当前图层的所有实体到新的DXF文档
        for entity in msp:
            if entity.dxf.layer == layer_name:
                new_entity = entity.copy()
                new_msp.add_entity(new_entity)

        # 保存新的DXF文件
        output_file_path = f"C:/Users/qjq/Desktop/imagekj/stonegeomerty/{layer_name}.dxf"
        try:
            new_doc.saveas(output_file_path)
            print(f"Layer '{layer_name}' saved to {output_file_path}")
        except IOError as e:
            print(f"Failed to save layer '{layer_name}': {e}")

# 调用函数并传入你的dxf文件路径
split_layers_to_dxf("C:/Users/qjq/Desktop/imagekj/stonegeomerty/SF5.dxf")

