"""GitHub-style study contribution heatmap."""

from __future__ import annotations

__all__ = [
    "load_showup_hours",
    "build_contribution_grid",
    "render_github_heatmap",
    "render_month_showup",
]

import calendar
import html
from datetime import date, timedelta

import pandas as pd

GITHUB_COLORS = ("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39")
DOW_LABELS = ("", "Mon", "", "Wed", "", "Fri", "")
WEEKS_TO_SHOW = 53


def load_showup_hours(start_date: date, end_date: date | None = None) -> dict[date, float]:
    from database import db_connection, get_current_user_id

    uid = get_current_user_id()
    if end_date is None:
        end_date = date.today()
    with db_connection(commit=False) as conn:
        df = pd.read_sql(
            """SELECT log_date, hours FROM daily_study_hours
               WHERE user_id = ? AND log_date >= ? AND log_date <= ?""",
            conn,
            params=(uid, start_date.isoformat(), end_date.isoformat()),
        )
    return {
        pd.to_datetime(row["log_date"]).date(): float(row["hours"])
        for _, row in df.iterrows()
    }


def _heat_level(hours: float, daily_goal: float) -> int:
    if hours <= 0:
        return 0
    if hours >= daily_goal:
        return 4
    if hours >= daily_goal * 0.5:
        return 3
    if hours >= 1:
        return 2
    return 1


def _grid_range(today: date | None = None) -> tuple[date, date, int]:
    today = today or date.today()
    grid_end = today
    grid_start = today - timedelta(days=364)
    grid_start -= timedelta(days=(grid_start.weekday() + 1) % 7)
    total_days = (grid_end - grid_start).days + 1
    weeks = (total_days + 6) // 7
    return grid_start, grid_end, weeks


def build_contribution_grid(
    hours_by_date: dict[date, float],
    *,
    daily_goal: float = 6.0,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    grid_start, grid_end, weeks = _grid_range(today)

    columns: list[list[dict]] = []
    month_labels: list[str] = []
    cursor = grid_start
    showups = 0
    total_hours = 0.0

    for _ in range(weeks):
        week: list[dict] = []
        for _ in range(7):
            in_range = grid_start <= cursor <= grid_end
            is_future = cursor > today
            hours = float(hours_by_date.get(cursor, 0) or 0) if in_range and not is_future else 0.0

            if in_range and not is_future:
                total_hours += hours
                if hours > 0:
                    showups += 1

            week.append({
                "date": cursor,
                "hours": hours,
                "level": _heat_level(hours, daily_goal) if in_range and not is_future else -1,
                "in_range": in_range,
                "is_future": is_future,
                "is_today": cursor == today,
            })
            cursor += timedelta(days=1)
        columns.append(week)

        week_dates = [cell["date"] for cell in week if cell["in_range"] and not cell["is_future"]]
        label = ""
        if week_dates:
            for d in week_dates:
                if d.day == 1:
                    label = calendar.month_abbr[d.month]
                    break
        month_labels.append(label)

    return {
        "columns": columns,
        "month_labels": month_labels,
        "weeks": weeks,
        "showups": showups,
        "total_hours": total_hours,
        "grid_start": grid_start,
        "grid_end": grid_end,
    }


def render_github_heatmap(
    hours_by_date: dict[date, float],
    *,
    streak: int = 0,
    daily_goal: float = 6.0,
    display_name: str = "Your",
) -> str:
    grid = build_contribution_grid(hours_by_date, daily_goal=daily_goal)
    cell = 11
    gap = 3
    col_w = cell + gap
    title_name = display_name if display_name.endswith("'s") else f"{display_name}'s"

    month_html = "".join(
        f'<span class="gh-month" style="width:{col_w}px">{html.escape(lbl)}</span>'
        for lbl in grid["month_labels"]
    )

    dow_html = "".join(
        f'<span class="gh-dow" style="height:{cell + gap}px">{html.escape(lbl)}</span>'
        for lbl in DOW_LABELS
    )

    cells: list[str] = []
    for column in grid["columns"]:
        for cell_data in column:
            d = cell_data["date"]
            if cell_data["is_future"] or not cell_data["in_range"]:
                cls = "gh-cell gh-empty"
                tip = ""
            else:
                level = cell_data["level"]
                cls = f"gh-cell gh-l{level}"
                if cell_data["is_today"]:
                    cls += " gh-today"
                if level == 0:
                    tip = f"No study on {d.strftime('%a, %d %b %Y')}"
                else:
                    tip = f"{cell_data['hours']:.1f}h on {d.strftime('%a, %d %b %Y')}"
            title = f' title="{html.escape(tip)}"' if tip else ""
            cells.append(f'<div class="{cls}"{title}></div>')

    colors_css = "\n".join(
        f".gh-l{i} {{ background: {GITHUB_COLORS[i]}; }}" for i in range(5)
    )

    return f"""<style>
  .gh-heatmap-root {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 12px;
    color: #24292f;
    margin-bottom: 0.5rem;
  }}
  .gh-heatmap-root * {{ box-sizing: border-box; }}
  .gh-wrap {{
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 16px;
    max-width: 100%;
  }}
  .gh-head {{
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 12px;
  }}
  .gh-title {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .gh-sub {{
    font-size: 12px;
    color: #57606a;
  }}
  .gh-sub strong {{ color: #24292f; }}
  .gh-legend {{
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 11px;
    color: #57606a;
  }}
  .gh-legend span {{ margin: 0 3px; }}
  .gh-legend .gh-cell {{
    width: 10px;
    height: 10px;
    border-radius: 2px;
  }}
  .gh-graph {{
    display: flex;
    gap: 4px;
    overflow-x: auto;
    padding-bottom: 2px;
  }}
  .gh-dows {{
    display: flex;
    flex-direction: column;
    padding-top: 15px;
    flex-shrink: 0;
  }}
  .gh-dow {{
    font-size: 9px;
    color: #57606a;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 4px;
    width: 28px;
  }}
  .gh-weeks {{
    flex: 1;
    min-width: 0;
  }}
  .gh-months {{
    display: flex;
    height: 15px;
    margin-bottom: 2px;
  }}
  .gh-month {{
    font-size: 9px;
    color: #57606a;
    flex-shrink: 0;
    overflow: visible;
    white-space: nowrap;
  }}
  .gh-grid {{
    display: grid;
    grid-auto-flow: column;
    grid-template-rows: repeat(7, {cell}px);
    gap: {gap}px;
    grid-auto-columns: {cell}px;
  }}
  .gh-cell {{
    width: {cell}px;
    height: {cell}px;
    border-radius: 2px;
    outline: 1px solid rgba(27, 31, 35, 0.06);
    outline-offset: -1px;
  }}
  .gh-empty {{
    background: transparent;
    outline: none;
  }}
  {colors_css}
  .gh-today {{
    outline: 1.5px solid #0969da;
    outline-offset: -1px;
  }}
  .gh-foot {{
    margin-top: 10px;
    font-size: 11px;
    color: #57606a;
  }}
</style>
<div class="gh-heatmap-root">
  <div class="gh-wrap">
    <div class="gh-head">
      <div>
        <div class="gh-title">{html.escape(title_name)} study activity</div>
        <div class="gh-sub">
          <strong>{grid['showups']}</strong> study days in the last year
          · <strong>{grid['total_hours']:.0f}h</strong> logged
          · <strong>{streak}</strong> day streak
        </div>
      </div>
      <div class="gh-legend">
        <span>Less</span>
        <div class="gh-cell gh-l0"></div>
        <div class="gh-cell gh-l1"></div>
        <div class="gh-cell gh-l2"></div>
        <div class="gh-cell gh-l3"></div>
        <div class="gh-cell gh-l4"></div>
        <span>More</span>
      </div>
    </div>
    <div class="gh-graph">
      <div class="gh-dows">{dow_html}</div>
      <div class="gh-weeks">
        <div class="gh-months">{month_html}</div>
        <div class="gh-grid">{''.join(cells)}</div>
      </div>
    </div>
    <div class="gh-foot">Goal: {daily_goal:g}h/day · darker green = more study logged</div>
  </div>
</div>"""


def render_month_showup(
    hours_by_date: dict[date, float],
    year: int,
    month: int,
    streak: int = 0,
    daily_goal: float = 6.0,
    display_name: str = "Your",
) -> str:
    """Backward-compatible alias — renders full GitHub year heatmap."""
    return render_github_heatmap(
        hours_by_date,
        streak=streak,
        daily_goal=daily_goal,
        display_name=display_name,
    )