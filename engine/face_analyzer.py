import numpy as np
from scipy.spatial import distance as dist

class FaceAnalyzer:
    # Índices do MediaPipe Face Mesh
    RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    MOUTH = [13, 14, 78, 308, 82, 312, 87, 317]

    @staticmethod
    def calcular_ear(landmarks, eye_indices):
        p = []
        for i in eye_indices:
            p.append([landmarks[i].x, landmarks[i].y])
        p = np.array(p)
        
        # EAR formula: distâncias verticais / distância horizontal
        v1 = dist.euclidean(p[12], p[4])
        v2 = dist.euclidean(p[11], p[5])
        h = dist.euclidean(p[0], p[8])
        return (v1 + v2) / (2.0 * h)

    @staticmethod
    def calcular_mar(landmarks):
        p = []
        for i in FaceAnalyzer.MOUTH:
            p.append([landmarks[i].x, landmarks[i].y])
        p = np.array(p)
        v = dist.euclidean(p[2], p[3])
        h = dist.euclidean(p[0], p[1])
        return v / h