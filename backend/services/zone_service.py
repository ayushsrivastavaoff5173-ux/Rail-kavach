from typing import List, Optional, Sequence, Tuple

import numpy as np

Point = Tuple[float, float]


def point_in_polygon(x: float, y: float, polygon: Sequence[Point]) -> bool:
    inside = False
    count = len(polygon)
    j = count - 1
    for i in range(count):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


class ZoneService:
    def __init__(self, name: str, polygon: Optional[list]) -> None:
        self.name = name
        self.polygon: Optional[List[Point]] = None

        if polygon is not None:
            points = [(float(x), float(y)) for x, y in polygon]
            if len(points) < 3:
                raise ValueError("ZONE_POLYGON needs at least 3 points")
            for x, y in points:
                if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                    raise ValueError("ZONE_POLYGON points must be between 0.0 and 1.0")
            self.polygon = points

    def contains(self, detection: Sequence[float], frame_width: int, frame_height: int) -> bool:
        if self.polygon is None:
            return True
        x1, y1, x2, y2 = detection[0], detection[1], detection[2], detection[3]
        foot_x = ((x1 + x2) / 2.0) / frame_width
        foot_y = y2 / frame_height
        return point_in_polygon(foot_x, foot_y, self.polygon)

    def polygon_pixels(self, frame_width: int, frame_height: int) -> Optional[np.ndarray]:
        if self.polygon is None:
            return None
        points = [[int(x * frame_width), int(y * frame_height)] for x, y in self.polygon]
        return np.array(points, dtype=np.int32).reshape((-1, 1, 2))