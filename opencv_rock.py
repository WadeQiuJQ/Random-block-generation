import math
import random
import numpy as np
import ezdxf
from shapely.geometry import Polygon
# 基础参数配置
AREA_WIDTH = 0.5
AREA_HEIGHT = 0.5

# 粒组定义：{粒径范围(min, max): 占比(%)}
GRAIN_GROUPS = {
    (0.06, 0.1): 9.83,
    (0.04, 0.06): 17.73,
    (0.02, 0.04): 20.90,
    (0.01, 0.02): 17.68,
    (0.005, 0.01): 13.85
}

# 块石边数范围
MIN_EDGES = 6
MAX_EDGES = 12

# 随机种子（固定以保证结果可复现，可注释以每次随机）
random.seed(42)
np.random.seed(42)

def generate_rock_diameter(d_min, d_max):
    urand = random.random()
    return d_min + urand * (d_max - d_min)

def generate_rock_position(diameter):
    r = diameter / 2
    xc = r + random.random() * (AREA_WIDTH - 2 * r)
    yc = r + random.random() * (AREA_HEIGHT - 2 * r)
    return xc, yc

def generate_convex_polygon_vertices(xc, yc, diameter, n_edges):
    vertices = []
    # 生成随机的顶点角度，不再均匀分布
    angles = sorted([random.uniform(0, 2 * math.pi) for _ in range(n_edges)])
    # 生成随机的半径变化因子，增加不规则性
    radius_factors = [random.uniform(0.7, 1.3) for _ in range(n_edges)]
    for i in range(n_edges):
        # 基于随机角度和随机半径因子生成顶点
        radius = (diameter / 2) * radius_factors[i]
        x = xc + radius * math.cos(angles[i])
        y = yc + radius * math.sin(angles[i])
        vertices.append((x, y))
    # 闭合多边形
    vertices.append(vertices[0])
    return vertices

def is_polygon_overlap(poly1, poly2):
    def get_aabb(poly):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return min(xs), min(ys), max(xs), max(ys)
    aabb1 = get_aabb(poly1)
    aabb2 = get_aabb(poly2)
    if (aabb1[2] < aabb2[0] or aabb1[0] > aabb2[2] or
            aabb1[3] < aabb2[1] or aabb1[1] > aabb2[3]):
        return False
    def point_in_polygon(point, poly):
        x, y = point
        inside = False
        n = len(poly) - 1
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[i+1]
            if ((y1 > y) != (y2 > y)):
                x_intersect = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                if x < x_intersect:
                    inside = not inside
        return inside
    for p in poly1[:-1]:
        if point_in_polygon(p, poly2):
            return True
    for p in poly2[:-1]:
        if point_in_polygon(p, poly1):
            return True

    def sah_or(poly1, poly2):
        return Polygon(poly1).intersects(Polygon(poly2))
    if sah_or(poly1, poly2):
        return True
    return False

def calculate_rock_area(vertices):
    area = 0.0
    n = len(vertices) - 1
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[i+1]
        area += (x1 * y2) - (x2 * y1)
    return abs(area) / 2.0

def generate_rock_blocks():
    rock_blocks = []
    total_area = AREA_WIDTH * AREA_HEIGHT
    for (d_min, d_max), ratio in GRAIN_GROUPS.items():
        target_area = total_area * (ratio / 100)
        current_area = 0.0
        max_attempts = 100000
        attempts = 0
        print(f"正在生成粒组 [{d_min}-{d_max}]（目标面积：{target_area:.4f}，占比{ratio}%）...")
        while current_area < target_area and attempts < max_attempts:
            attempts += 1
            diameter = generate_rock_diameter(d_min, d_max)
            xc, yc = generate_rock_position(diameter)
            n_edges = random.randint(MIN_EDGES, MAX_EDGES)
            vertices = generate_convex_polygon_vertices(xc, yc, diameter, n_edges)
            overlap = False
            for existing_rock in rock_blocks:
                if is_polygon_overlap(vertices, existing_rock["vertices"]):
                    overlap = True
                    break
            if overlap:
                continue
            rock_area = calculate_rock_area(vertices)
            current_area += rock_area
            rock_blocks.append({
                "grain_group": f"{d_min}-{d_max}",
                "diameter": diameter,
                "edges": n_edges,
                "area": rock_area,
                "vertices": vertices
            })
        actual_ratio = (current_area / total_area) * 100
        print(f"粒组 [{d_min}-{d_max}] 生成完成：实际面积{current_area:.4f}，实际占比{actual_ratio:.2f}%（尝试次数：{attempts}）")
    return rock_blocks

def export_to_dxf(rock_blocks, filename="HSL80.dxf"):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    layer_colors = {
        "0.06-0.1": 1,
        "0.04-0.06": 2,
        "0.02-0.04": 3,
        "0.01-0.02": 4,
        "0.005-0.01": 5,
    }
    for grain_group, color in layer_colors.items():
        doc.layers.new(name=f"Grain_{grain_group}", dxfattribs={"color": color})
    for rock in rock_blocks:
        grain_group = rock["grain_group"]
        vertices = rock["vertices"]
        layer_name = f"Grain_{grain_group}"
        msp.add_lwpolyline(
            points=[(p[0], p[1]) for p in vertices],
            dxfattribs={
                "layer": layer_name,
                "closed": True,
                "color": layer_colors[grain_group]
            }
        )
    doc.saveas(filename)
    print(f"DXF文件已保存：{filename}")
    print(f"共生成 {len(rock_blocks)} 个块石")

if __name__ == "__main__":
    rock_blocks = generate_rock_blocks()
    export_to_dxf(rock_blocks)
