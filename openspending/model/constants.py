
DATE_CUBES_TEMPLATE = {
    "role": "time",
    "levels": [
        {
            "name": "year",
            "label": "Year"
        },
        {
            "name": "quarter",
            "label": "Quarter"
        },
        {
            "name": "month",
            "label": "Month"
        },
        {
            "name": "week",
            "label": "Week"
        },
        {
            "name": "day",
            "label": "Day",
            "key": "name",
            "attributes": ['day', 'name']
        }
    ],
    "hierarchies": [
        {
            "name": "weekly",
            "label": "Weekly",
            "levels": ["year", "week"]
        },
        {
            "name": "daily",
            "label": "Daily",
            "levels": ["year", "month", "day"]
        },
        {
            "name": "monthly",
            "label": "Monthly",
            "levels": ["year", "quarter", "month"]
        }
    ]
}
