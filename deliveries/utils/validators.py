def validate_lat_lon_input(location):
    """
    Validate and format location input.
    Args:
        location: The location input to validate.
    Returns:
        dict: A GeoJSON Point object.
    Raises:
        ValueError: If the location format is invalid.
    """
    if not isinstance(location, dict):
        raise ValueError("Location must be a dictionary")

    if location.get("type") != "Point":
        raise ValueError("Location type must be 'Point'")

    coords = location.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        raise ValueError("Coordinates must be a list of [longitude, latitude]")

    try:
        lon, lat = float(coords[0]), float(coords[1])
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            raise ValueError("Invalid coordinate values")
    except (ValueError, TypeError):
        raise ValueError("Coordinates must be numeric values")

    return {
        "type": "Point",
        "coordinates": [lon, lat]
    }
