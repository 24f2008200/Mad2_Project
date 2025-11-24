from typing import Any, Callable, Dict, Iterable, List

def serialize_model(instance: Any, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model using its to_dict() if available, plus optional extra fields."""
    if instance is None:
        return {}
    if hasattr(instance, "to_dict"):
        data = instance.to_dict()
    else:
        # Fallback: use __dict__ minus private fields
        data = {
            k: v for k, v in vars(instance).items()
            if not k.startswith("_")
        }
    if extra:
        data.update(extra)
    return data


def serialize_list(
    items: Iterable[Any],
    extra_fn: Callable[[Any], Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """Serialize a list of model instances with optional per-item extra fields."""
    out: List[Dict[str, Any]] = []
    for item in items:
        extra = extra_fn(item) if extra_fn else None
        out.append(serialize_model(item, extra))
    return out
