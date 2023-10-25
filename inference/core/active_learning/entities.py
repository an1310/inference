from dataclasses import dataclass
from enum import Enum
from typing import Any, Tuple, Optional, Callable, List, Dict

import numpy as np

from inference.core.entities.types import WorkspaceID, DatasetID

LocalImageIdentifier = str
PredictionType = str
Prediction = dict


@dataclass(frozen=True)
class ImageDimensions:
    height: int
    width: int

    def to_hw(self) -> Tuple[int, int]:
        return self.height, self.width

    def to_wh(self) -> Tuple[int, int]:
        return self.width, self.height


@dataclass(frozen=True)
class SamplingResult:
    datapoint_selected: bool
    target_split: Optional[str] = None


@dataclass(frozen=True)
class SamplingMethod:
    name: str
    sample: Callable[[np.ndarray, Prediction, PredictionType], bool]


class BatchReCreationInterval(Enum):
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class StrategyLimitType(Enum):
    HOURLY = "hourly"
    DAILY = "daily"


@dataclass(frozen=True)
class StrategyLimit:
    limit_type: StrategyLimitType
    value: int

    @classmethod
    def from_dict(cls, specification: dict) -> "StrategyLimit":
        return cls(
            limit_type=StrategyLimitType(specification["type"]),
            value=specification["value"],
        )


@dataclass(frozen=True)
class ActiveLearningConfiguration:
    max_image_size: Optional[ImageDimensions]
    jpeg_compression_level: int
    persist_predictions: bool
    sampling_methods: List[SamplingMethod]
    batches_name_prefix: str
    batch_recreation_interval: BatchReCreationInterval
    max_batch_images: Optional[int]
    workspace_id: WorkspaceID
    dataset_id: DatasetID
    model_id: str
    strategies_limits: Dict[str, List[StrategyLimit]]
    tags: List[str]
    strategies_tags: Dict[str, List[str]]

    @classmethod
    def init(
        cls,
        roboflow_api_configuration: Dict[str, Any],
        sampling_methods: List[SamplingMethod],
        workspace_id: WorkspaceID,
        dataset_id: DatasetID,
        model_id: str,
    ) -> "ActiveLearningConfiguration":
        try:
            max_image_size = roboflow_api_configuration.get("max_image_size")
            if max_image_size is not None:
                max_image_size = ImageDimensions(
                    height=roboflow_api_configuration["max_image_size"][0],
                    width=roboflow_api_configuration["max_image_size"][1],
                )
            strategies_limits = {
                strategy["name"]: [
                    StrategyLimit.from_dict(specification=specification)
                    for specification in strategy["limits"]
                ]
                for strategy in roboflow_api_configuration["sampling_strategies"]
            }
            strategies_tags = {
                strategy["name"]: strategy.get("tags", [])
                for strategy in roboflow_api_configuration["sampling_strategies"]
            }
            return cls(
                max_image_size=max_image_size,
                jpeg_compression_level=roboflow_api_configuration[
                    "jpeg_compression_level"
                ],
                persist_predictions=roboflow_api_configuration["persist_predictions"],
                sampling_methods=sampling_methods,
                batches_name_prefix=roboflow_api_configuration["batching_strategy"][
                    "batches_name_prefix"
                ],
                batch_recreation_interval=BatchReCreationInterval(
                    roboflow_api_configuration["batching_strategy"][
                        "recreation_interval"
                    ]
                ),
                max_batch_images=roboflow_api_configuration["batching_strategy"][
                    "max_batch_images"
                ],
                workspace_id=workspace_id,
                dataset_id=dataset_id,
                model_id=model_id,
                strategies_limits=strategies_limits,
                tags=roboflow_api_configuration.get("tags", []),
                strategies_tags=strategies_tags,
            )
        except (KeyError, ValueError) as e:
            raise Exception(str(e)) from e
