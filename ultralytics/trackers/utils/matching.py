# Ultralytics YOLO 🚀, AGPL-3.0 license

import numpy as np
import scipy
from ultralytics.utils.metrics import bbox_ioa
from scipy.spatial.distance import cdist

try:
    import lap  # for linear_assignment

    assert lap.__version__  # verify package is not directory
except (ImportError, AssertionError, AttributeError):
    from ultralytics.utils.checks import check_requirements

    check_requirements('lapx>=0.5.2')  # update to lap package from https://github.com/rathaROG/lapx
    import lap


def linear_assignment(cost_matrix, thresh, use_lap=True):
    """Linear assignment implementations with scipy and lap.lapjv."""
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), tuple(range(cost_matrix.shape[0])), tuple(range(cost_matrix.shape[1]))

    if use_lap:
        _, x, y = lap.lapjv(cost_matrix, extend_cost=True, cost_limit=thresh)
        matches = [[ix, mx] for ix, mx in enumerate(x) if mx >= 0]
        unmatched_a = np.where(x < 0)[0]
        unmatched_b = np.where(y < 0)[0]
    else:
        # Scipy linear sum assignment is NOT working correctly, DO NOT USE
        y, x = scipy.optimize.linear_sum_assignment(cost_matrix)  # row y, col x
        matches = np.asarray([[i, x] for i, x in enumerate(x) if cost_matrix[i, x] <= thresh])
        unmatched = np.ones(cost_matrix.shape)
        for i, xi in matches:
            unmatched[i, xi] = 0.0
        unmatched_a = np.where(unmatched.all(1))[0]
        unmatched_b = np.where(unmatched.all(0))[0]

    return matches, unmatched_a, unmatched_b


def iou_distance(atracks, btracks):
    """
    Compute cost based on IoU
    :type atracks: list[STrack]
    :type btracks: list[STrack]

    :rtype cost_matrix np.ndarray
    """

    if (len(atracks) > 0 and isinstance(atracks[0], np.ndarray)) \
            or (len(btracks) > 0 and isinstance(btracks[0], np.ndarray)):
        atlbrs = atracks
        btlbrs = btracks
    else:
        atlbrs = [track.tlbr for track in atracks]
        btlbrs = [track.tlbr for track in btracks]

    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    if len(atlbrs) or len(btlbrs):
        ious = bbox_ioa(np.ascontiguousarray(atlbrs, dtype=np.float32), 
                        np.ascontiguousarray(btlbrs, dtype=np.float32), iou=True)
    return 1 - ious  # cost matrix


def embedding_distance(tracks, detections, metric='cosine'):
    """
    :param tracks: list[STrack]
    :param detections: list[BaseTrack]
    :param metric:
    :return: cost_matrix np.ndarray
    """

    cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
    if cost_matrix.size == 0:
        return cost_matrix
    det_features = np.asarray([track.curr_feat for track in detections], dtype=np.float32)
    # for i, track in enumerate(tracks):
    # cost_matrix[i, :] = np.maximum(0.0, cdist(track.smooth_feat.reshape(1,-1), det_features, metric))
    track_features = np.asarray([track.smooth_feat for track in tracks], dtype=np.float32)
    cost_matrix = np.maximum(0.0, cdist(track_features, det_features, metric))  # Normalized features
    return cost_matrix


def fuse_score(cost_matrix, detections):
    """Fuses cost matrix with detection scores to produce a single similarity matrix."""
    if cost_matrix.size == 0:
        return cost_matrix
    iou_sim = 1 - cost_matrix
    det_scores = np.array([det.score for det in detections])
    det_scores = np.expand_dims(det_scores, axis=0).repeat(cost_matrix.shape[0], axis=0)
    fuse_sim = iou_sim * det_scores
    return 1 - fuse_sim  # fuse_cost
