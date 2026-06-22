from __future__ import annotations

import json

from app.quality import evaluate_quality


if __name__ == "__main__":
    print(json.dumps(evaluate_quality().model_dump(by_alias=True, mode="json"), indent=2))
