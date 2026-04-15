---
name: create-garmin-workout
description: >
  Use this skill when the user asks to "create a workout", "add a workout to Garmin",
  "schedule a run", "make an interval session", "plan a training session", "create an
  easy run", "build a tempo run", "set up a long run", or any request to define and
  save a structured workout on Garmin Connect. Also triggers when the user describes
  a workout in natural language and wants it pushed to their watch calendar.
metadata:
  version: "0.1.0"
---

# Garmin Workout Creation

Translate the user's natural language workout description into a `garmin_create_running_workout` tool call. Follow these steps:

## 1. Parse the description

Extract:
- **Workout type**: easy run, tempo, intervals, long run, trail run, etc.
- **Distance or duration**: km, miles, minutes, hours
- **Effort/HR target**: zone number (Z1–Z5), "easy", "moderate", "threshold", "max"
- **Structure**: warmup + main + cooldown, or repeat intervals
- **Schedule date**: "tomorrow", "Saturday", "April 11", specific date

## 2. Map effort to HR zones

| User says | hr_zone | Notes |
|-----------|---------|-------|
| easy, recovery, Z1 | 1 | Very light |
| easy aerobic, Z2 | 2 | Conversational pace — most common for long runs |
| moderate, aerobic, Z3 | 3 | Comfortably hard |
| tempo, threshold, hard, Z4 | 4 | Can speak in short sentences |
| max effort, race pace, Z5 | 5 | Near maximum |

If no HR target is specified, leave `hr_zone` and `hr_bpm_*` null (applies to warmup and cooldown too).

## 3. Build the step structure

**Simple run** (easy run, tempo, long run):
```
warmup:     { step_type: "warmup",   duration_type: "distance", duration_value: 1000 }
main_steps: [{ step_type: "interval", duration_type: "distance", duration_value: <meters>, hr_zone: <zone> }]
cooldown:   { step_type: "cooldown", duration_type: "distance", duration_value: 1000 }
```

**Time-based** (2 hours, 45 minutes, etc.):
```
main_steps: [{ step_type: "interval", duration_type: "time", duration_value: <seconds>, hr_zone: <zone> }]
```

**Repeat intervals** (5×1km, 10×400m, etc.):
```
main_steps: [{
  iterations: <N>,
  steps: [
    { step_type: "interval", duration_type: "distance", duration_value: <meters>, hr_zone: <zone> },
    { step_type: "recovery", duration_type: "distance", duration_value: <recovery_meters> }
  ]
}]
```

**Loop/mountain run with repeats** (e.g. 3 loops of 36 min):
```
warmup:     { step_type: "warmup",   duration_type: "time", duration_value: 600 }
main_steps: [{
  iterations: 3,
  steps: [
    { step_type: "interval", duration_type: "time", duration_value: 2160, hr_zone: 2 },
    { step_type: "recovery", duration_type: "time", duration_value: 60 }
  ]
}]
cooldown:   { step_type: "cooldown", duration_type: "time", duration_value: 360 }
```

## 4. Unit conversions

| Input | duration_type | duration_value |
|-------|---------------|----------------|
| 8 km | distance | 8000 |
| 5 miles | distance | 8047 |
| 1 km | distance | 1000 |
| 400 m | distance | 400 |
| 10 min | time | 600 |
| 1 hour | time | 3600 |
| 2 hours | time | 7200 |
| 36 min | time | 2160 |

## 5. Naming the workout

Use a clear, descriptive name:
- "Easy Run 8km — Zone 2"
- "Interval 5×1km — Zone 4"
- "Šljeme Long Run — 3 Loops"
- "Tempo Run 10km"

## 6. Call the tool

Call `garmin_create_running_workout` with all fields. Always include `schedule_date` if the user mentioned a date.

After success, confirm the workout name, schedule date, and share the Garmin Connect link from the response.

## Reference

See `references/workout-types.md` for more examples of common workout patterns.
