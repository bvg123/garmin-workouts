#!/usr/bin/env python3
"""
Garmin Workouts MCP Server
Provides tools to create, schedule, list and delete workouts on Garmin Connect.
Auth: Reuses OAuth tokens from ~/.garth (shared with the main Garmin MCP connector).
"""

import subprocess
import sys

# ── Auto-install dependencies before any other imports ───────────────────────
_DEPS = {"mcp": "mcp[cli]", "garminconnect": "garminconnect", "pydantic": "pydantic"}
for _import_name, _pkg_name in _DEPS.items():
    try:
        __import__(_import_name)
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", _pkg_name, "-q"],
            stderr=subprocess.DEVNULL,
        )

# ── Imports ───────────────────────────────────────────────────────────────────
import asyncio
import json
import os
from typing import Optional, Union

import garminconnect
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Server ────────────────────────────────────────────────────────────────────
mcp = FastMCP("garmin_workouts_mcp")

# ── Garmin client (lazy singleton) ────────────────────────────────────────────
_client: Optional[garminconnect.Garmin] = None


def _get_api() -> garminconnect.Garmin:
    global _client
    if _client is None:
        garth_home = os.path.expanduser("~/.garth")

        if not os.path.isdir(garth_home):
            raise RuntimeError(
                "No saved Garmin session found at ~/.garth. "
                "Please authenticate via the main Garmin MCP connector first — "
                "it will create the OAuth tokens that this server reuses."
            )

        try:
            _client = garminconnect.Garmin()
            _client.login(tokenstore=garth_home)
        except Exception as e:
            _client = None
            raise RuntimeError(
                f"Failed to authenticate with saved tokens at ~/.garth: {e}. "
                "Try reconnecting the main Garmin MCP connector to refresh tokens."
            ) from e
    return _client


# ── Workout payload builders ──────────────────────────────────────────────────
_STEP_TYPES = {
    "warmup":   {"stepTypeId": 1, "stepTypeKey": "warmup",   "displayOrder": 1},
    "cooldown": {"stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2},
    "interval": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
    "recovery": {"stepTypeId": 4, "stepTypeKey": "recovery", "displayOrder": 4},
    "rest":     {"stepTypeId": 5, "stepTypeKey": "rest",     "displayOrder": 5},
}

_RUNNING_SPORT = {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1}

# Approximate HR zone BPM ranges (Garmin will use user's personal zones when
# zoneNumber is provided; BPM values serve as a sensible fallback display).
_ZONE_BPM = {1: (100, 120), 2: (120, 143), 3: (143, 160), 4: (160, 174), 5: (174, 195)}


def _build_target(
    hr_zone: Optional[int],
    hr_bpm_low: Optional[float],
    hr_bpm_high: Optional[float],
) -> dict:
    if hr_zone is not None:
        lo, hi = _ZONE_BPM.get(hr_zone, (100, 200))
        if hr_bpm_low is not None:
            lo = hr_bpm_low
        if hr_bpm_high is not None:
            hi = hr_bpm_high
        return {
            "workoutTargetTypeId": 4,
            "workoutTargetTypeKey": "heart.rate.zone",
            "displayOrder": 1,
            "zoneNumber": hr_zone,
            "targetValueLow": float(lo),
            "targetValueHigh": float(hi),
        }
    if hr_bpm_low is not None and hr_bpm_high is not None:
        return {
            "workoutTargetTypeId": 4,
            "workoutTargetTypeKey": "heart.rate.zone",
            "displayOrder": 1,
            "targetValueLow": float(hr_bpm_low),
            "targetValueHigh": float(hr_bpm_high),
        }
    return {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}


def _build_end_condition(duration_type: str, value: float) -> tuple[dict, float]:
    if duration_type == "time":
        return (
            {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
            float(value),
        )
    # distance
    return (
        {"conditionTypeId": 1, "conditionTypeKey": "distance", "displayOrder": 2, "displayable": True},
        float(value),
    )


def _build_executable_step(order: int, step) -> dict:
    end_cond, end_val = _build_end_condition(step.duration_type, step.duration_value)
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": order,
        "stepType": _STEP_TYPES[step.step_type],
        "endCondition": end_cond,
        "endConditionValue": end_val,
        "targetType": _build_target(step.hr_zone, step.hr_bpm_low, step.hr_bpm_high),
    }


def _build_repeat_group(order: int, iterations: int, inner_steps: list[dict]) -> dict:
    return {
        "type": "RepeatGroupDTO",
        "stepOrder": order,
        "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
        "numberOfIterations": iterations,
        "workoutSteps": inner_steps,
        "endCondition": {
            "conditionTypeId": 7, "conditionTypeKey": "iterations",
            "displayOrder": 7, "displayable": False,
        },
        "endConditionValue": float(iterations),
    }


def _assemble_steps(warmup, main_steps, cooldown) -> list[dict]:
    result = []
    order = 1
    if warmup:
        result.append(_build_executable_step(order, warmup))
        order += 1
    for item in main_steps:
        if isinstance(item, RepeatGroupModel):
            inner = [_build_executable_step(i + 1, s) for i, s in enumerate(item.steps)]
            result.append(_build_repeat_group(order, item.iterations, inner))
        else:
            result.append(_build_executable_step(order, item))
        order += 1
    if cooldown:
        result.append(_build_executable_step(order, cooldown))
    return result


# ── Pydantic models ───────────────────────────────────────────────────────────

class WorkoutStep(BaseModel):
    """A single executable step in a workout."""
    model_config = ConfigDict(str_strip_whitespace=True)

    step_type: str = Field(
        ...,
        description=(
            "Step type: 'warmup', 'interval', 'recovery', 'cooldown', or 'rest'. "
            "Use 'interval' for the main effort block, 'recovery' for rest between intervals."
        ),
    )
    duration_type: str = Field(
        ...,
        description="'time' (value = seconds) or 'distance' (value = meters).",
    )
    duration_value: float = Field(
        ...,
        description=(
            "Duration in seconds (time) or meters (distance). "
            "Examples: 600=10min, 1800=30min, 1000=1km, 8000=8km."
        ),
        gt=0,
    )
    hr_zone: Optional[int] = Field(
        default=None,
        description=(
            "Heart rate zone target 1-5 using user's personal Garmin zones. "
            "Zone 2 = easy aerobic. Zone 3 = moderate. Zone 4 = threshold. "
            "Leave null for no HR target (e.g. warmup/cooldown)."
        ),
        ge=1, le=5,
    )
    hr_bpm_low: Optional[float] = Field(
        default=None,
        description="Custom HR lower bound in bpm (only if you need exact bpm instead of a zone).",
        ge=60, le=220,
    )
    hr_bpm_high: Optional[float] = Field(
        default=None,
        description="Custom HR upper bound in bpm (only if you need exact bpm instead of a zone).",
        ge=60, le=220,
    )

    @field_validator("step_type")
    @classmethod
    def _valid_step_type(cls, v: str) -> str:
        if v.lower() not in _STEP_TYPES:
            raise ValueError(f"step_type must be one of {sorted(_STEP_TYPES)}")
        return v.lower()

    @field_validator("duration_type")
    @classmethod
    def _valid_duration_type(cls, v: str) -> str:
        if v.lower() not in {"time", "distance"}:
            raise ValueError("duration_type must be 'time' or 'distance'")
        return v.lower()


class RepeatGroupModel(BaseModel):
    """A group of steps repeated N times (use for intervals)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    iterations: int = Field(
        ...,
        description="Number of repetitions (e.g. 5 for 5x1km).",
        ge=2, le=50,
    )
    steps: list[WorkoutStep] = Field(
        ...,
        description=(
            "Steps inside the repeat block. Typically [interval_step, recovery_step]. "
            "Example: [{step_type:'interval', duration_type:'distance', duration_value:1000, hr_zone:4}, "
            "{step_type:'recovery', duration_type:'distance', duration_value:200}]"
        ),
        min_length=1,
    )


class CreateRunningWorkoutInput(BaseModel):
    """Input for garmin_create_running_workout."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    workout_name: str = Field(
        ...,
        description="Workout name on Garmin Connect (e.g. 'Easy Run 8km - Zone 2').",
        min_length=1, max_length=100,
    )
    description: str = Field(
        default="",
        description="Optional notes shown in Garmin Connect.",
        max_length=500,
    )
    warmup: Optional[WorkoutStep] = Field(
        default=None,
        description=(
            "Optional warm-up step. Typically 1-2 km or 5-10 min, no HR target. "
            "Example: {step_type:'warmup', duration_type:'distance', duration_value:1000}"
        ),
    )
    main_steps: list[Union[WorkoutStep, RepeatGroupModel]] = Field(
        ...,
        description=(
            "Main workout body. Each item is either a WorkoutStep or a RepeatGroupModel.\n"
            "WorkoutStep - single continuous block:\n"
            "  {step_type:'interval', duration_type:'distance', duration_value:6000, hr_zone:2}\n"
            "RepeatGroupModel - repeated intervals:\n"
            "  {iterations:5, steps:[{step_type:'interval',...1000m, hr_zone:4}, {step_type:'recovery',...200m}]}"
        ),
        min_length=1,
    )
    cooldown: Optional[WorkoutStep] = Field(
        default=None,
        description=(
            "Optional cool-down step. Typically 1-2 km or 5 min, no HR target. "
            "Example: {step_type:'cooldown', duration_type:'distance', duration_value:1000}"
        ),
    )
    estimated_duration_secs: int = Field(
        default=0,
        description="Estimated total duration in seconds (display only). Use 0 to skip.",
        ge=0,
    )
    schedule_date: Optional[str] = Field(
        default=None,
        description=(
            "Date to schedule this workout on the Garmin Connect calendar (YYYY-MM-DD). "
            "Omit to save without scheduling. Example: '2026-04-11'."
        ),
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )


class WorkoutIdInput(BaseModel):
    """Input for operations on an existing workout."""
    model_config = ConfigDict(str_strip_whitespace=True)
    workout_id: str = Field(..., description="Workout ID (from garmin_list_workouts).")


class ScheduleWorkoutInput(BaseModel):
    """Input for scheduling an existing workout."""
    model_config = ConfigDict(str_strip_whitespace=True)
    workout_id: str = Field(..., description="Workout ID to schedule (from garmin_list_workouts).")
    date: str = Field(
        ...,
        description="Date to schedule (YYYY-MM-DD).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool(
    name="garmin_create_running_workout",
    annotations={
        "title": "Create Running Workout on Garmin Connect",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def garmin_create_running_workout(params: CreateRunningWorkoutInput) -> str:
    """Create a structured running workout on Garmin Connect and optionally schedule it."""
    try:
        steps = _assemble_steps(params.warmup, params.main_steps, params.cooldown)
        payload = {
            "workoutName": params.workout_name,
            "description": params.description,
            "sportType": _RUNNING_SPORT,
            "estimatedDurationInSecs": params.estimated_duration_secs,
            "workoutSegments": [{
                "segmentOrder": 1,
                "sportType": _RUNNING_SPORT,
                "workoutSteps": steps,
            }],
        }

        api = await asyncio.to_thread(_get_api)
        result = await asyncio.to_thread(api.upload_workout, payload)

        workout_id = (
            result.get("workoutId")
            or result.get("workout", {}).get("workoutId")
        )
        if not workout_id:
            return f"Workout created but ID not found in response: {str(result)[:300]}"

        lines = [
            f"Workout '{params.workout_name}' created (ID: {workout_id}).",
            f"Link: https://connect.garmin.com/modern/workout/{workout_id}",
        ]

        if params.schedule_date:
            await asyncio.to_thread(api.schedule_workout, workout_id, params.schedule_date)
            lines.append(f"Scheduled for {params.schedule_date}.")

        return "\n".join(lines)

    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="garmin_list_workouts",
    annotations={
        "title": "List Saved Garmin Workouts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_list_workouts() -> str:
    """List all saved workouts on Garmin Connect."""
    try:
        api = await asyncio.to_thread(_get_api)
        workouts = await asyncio.to_thread(api.get_workouts)
        if not workouts:
            return "No saved workouts found on Garmin Connect."

        lines = [f"Saved Workouts ({len(workouts)} total)\n"]
        for w in workouts[:50]:
            wid = w.get("workoutId", "?")
            name = w.get("workoutName", "Unnamed")
            sport = w.get("sportType", {}).get("sportTypeKey", "?")
            created = str(w.get("createDate", ""))[:10]
            lines.append(f"- {name} | ID: {wid} | {sport} | {created}")
        return "\n".join(lines)

    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="garmin_schedule_workout",
    annotations={
        "title": "Schedule an Existing Garmin Workout",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def garmin_schedule_workout(params: ScheduleWorkoutInput) -> str:
    """Schedule an existing saved workout on a specific date in the Garmin Connect calendar."""
    try:
        api = await asyncio.to_thread(_get_api)
        await asyncio.to_thread(api.schedule_workout, params.workout_id, params.date)
        return f"Workout {params.workout_id} scheduled for {params.date}."
    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="garmin_delete_workout",
    annotations={
        "title": "Delete a Garmin Workout",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def garmin_delete_workout(params: WorkoutIdInput) -> str:
    """Delete a saved workout from Garmin Connect. This cannot be undone."""
    try:
        api = await asyncio.to_thread(_get_api)
        await asyncio.to_thread(api.delete_workout, params.workout_id)
        return f"Workout {params.workout_id} deleted."
    except RuntimeError as e:
        return f"Configuration error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
