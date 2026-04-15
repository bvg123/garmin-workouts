# Common Workout Patterns

## Easy Run (any distance)
```json
{
  "workout_name": "Easy Run 8km — Zone 2",
  "warmup": { "step_type": "warmup", "duration_type": "distance", "duration_value": 1000 },
  "main_steps": [{ "step_type": "interval", "duration_type": "distance", "duration_value": 6000, "hr_zone": 2 }],
  "cooldown": { "step_type": "cooldown", "duration_type": "distance", "duration_value": 1000 },
  "estimated_duration_secs": 3000,
  "schedule_date": "2026-04-11"
}
```

## Tempo Run
```json
{
  "workout_name": "Tempo Run 6km — Zone 4",
  "warmup": { "step_type": "warmup", "duration_type": "distance", "duration_value": 2000 },
  "main_steps": [{ "step_type": "interval", "duration_type": "distance", "duration_value": 6000, "hr_zone": 4 }],
  "cooldown": { "step_type": "cooldown", "duration_type": "distance", "duration_value": 2000 },
  "estimated_duration_secs": 3600
}
```

## Classic Intervals (e.g. 5×1km)
```json
{
  "workout_name": "Interval 5×1km — Zone 4",
  "warmup": { "step_type": "warmup", "duration_type": "distance", "duration_value": 2000 },
  "main_steps": [{
    "iterations": 5,
    "steps": [
      { "step_type": "interval", "duration_type": "distance", "duration_value": 1000, "hr_zone": 4 },
      { "step_type": "recovery", "duration_type": "distance", "duration_value": 400 }
    ]
  }],
  "cooldown": { "step_type": "cooldown", "duration_type": "distance", "duration_value": 1000 },
  "estimated_duration_secs": 3600
}
```

## Long Run (time-based)
```json
{
  "workout_name": "Long Run 90min — Zone 2",
  "warmup": { "step_type": "warmup", "duration_type": "time", "duration_value": 600 },
  "main_steps": [{ "step_type": "interval", "duration_type": "time", "duration_value": 4800, "hr_zone": 2 }],
  "cooldown": { "step_type": "cooldown", "duration_type": "time", "duration_value": 600 },
  "estimated_duration_secs": 6000
}
```

## Mountain / Trail Run with Loops
```json
{
  "workout_name": "Šljeme — Scouting Long Run",
  "description": "3 loops ~5km/~200m each. Walk uphills. Stop after any loop if over 2h.",
  "warmup": { "step_type": "warmup", "duration_type": "time", "duration_value": 600 },
  "main_steps": [{
    "iterations": 3,
    "steps": [
      { "step_type": "interval", "duration_type": "time", "duration_value": 2160, "hr_zone": 2 },
      { "step_type": "recovery", "duration_type": "time", "duration_value": 60 }
    ]
  }],
  "cooldown": { "step_type": "cooldown", "duration_type": "time", "duration_value": 360 },
  "estimated_duration_secs": 7200
}
```

## Fartlek / Unstructured Run
```json
{
  "workout_name": "Fartlek 45min",
  "main_steps": [{ "step_type": "interval", "duration_type": "time", "duration_value": 2700 }],
  "estimated_duration_secs": 2700
}
```

## HR Zone Reference (approximate for VO2max ~48)
| Zone | BPM Range | Feel |
|------|-----------|------|
| Z1 | 100–120 | Very easy, recovery |
| Z2 | 120–143 | Easy, conversational |
| Z3 | 143–160 | Moderate, comfortably hard |
| Z4 | 160–174 | Hard, tempo/threshold |
| Z5 | 174+ | Max effort, short intervals |
