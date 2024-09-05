


class CameraCalibModel:
    def __init__(self)->None:
        self.__boundary_points = [
            (0,0),
            (0.9, 0),
            (0.9, 0.5),
            (0, 0.2)
        ]
        self.__mask_polys = [
            # List of polygons points
        ]

        self.__data = {
            "poly_points":self.__boundary_points,
            "mask_polys": self.__mask_polys
        }

    def get_data(self)->dict:
        return self.__data

    def get_boundary_points(self)->None:
        return self.__boundary_points
    
    def set_boundary_points(self, points:list[tuple[float]])->None:
        self.__boundary_points = points
        self.__data['poly_points'] = self.__boundary_points

    def set_mask_polys(self, mask_polys)->None:
        self.__mask_polys = mask_polys
        self.__data['mask_polys'] = self.__mask_polys

    