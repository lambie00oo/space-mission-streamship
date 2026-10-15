import math

import streamlit as st

from data.planets import Planet
from logic.rendezvous import (
    RENDEZVOUS_TOLERANCE_KM,
    fine_tune_angle_degrees,
    normalize_angle_degrees,
    shortest_angle_difference_degrees,
)
from ui.orbit_plot import mission2_orbit_simulation


COMPONENT_KEY = "m3_rendezvous_component"
HTML = '<div class="mission3-rendezvous"></div>'
CSS = """
.mission3-rendezvous {
  color: #f2f7ff;
  font-family: sans-serif;
  background: #0b1b33;
  border: 1px solid #315575;
  border-radius: 12px;
  padding: 16px;
}
.rendezvous-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(220px, 1fr);
  gap: 18px;
  align-items: start;
}
.rendezvous-plot svg {
  display: block;
  width: 100%;
  min-height: 300px;
  touch-action: none;
  background: #071426;
  border: 1px solid #24415f;
  border-radius: 10px;
}
.rendezvous-orbit { fill: none; stroke: #68809a; stroke-dasharray: 3 5; }
.rendezvous-transfer { fill: none; stroke: #ff8c42; stroke-width: 2.5; }
.rendezvous-target { stroke: #d6c27a; stroke-width: 1.5; stroke-dasharray: 6 5; }
.rendezvous-handle { fill: #d65353; stroke: #fff; stroke-width: 2; cursor: grab; }
.rendezvous-handle:active { cursor: grabbing; }
.rendezvous-ship { fill: #fff; stroke: #50c8ff; stroke-width: 3; }
.rendezvous-earth { fill: #4ea5d9; stroke: #fff; stroke-width: 1.5; }
.rendezvous-sun { fill: #ffcc33; stroke: #e08a00; stroke-width: 2; }
.rendezvous-label { fill: #f2f7ff; font-size: 13px; }
.rendezvous-stats {
  background: #102742;
  border: 1px solid #315575;
  border-radius: 9px;
  padding: 12px;
}
.rendezvous-stats h4 { color: #b9efff; margin: 0 0 8px; }
.rendezvous-stats p { margin: 7px 0; font-size: 0.9rem; }
.rendezvous-controls { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.rendezvous-controls button {
  background: #102742;
  border: 1px solid #50c8ff;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 8px 11px;
}
.rendezvous-controls button:hover { background: #0877b9; }
.rendezvous-note { color: #b9efff; font-size: 0.83rem; margin-top: 10px; }
@media (max-width: 760px) {
  .rendezvous-layout { grid-template-columns: 1fr; }
}
"""
JS = """
export default function(component) {
  const { data, setStateValue, parentElement } = component;
  const root = parentElement.querySelector('.mission3-rendezvous');
  let state = parentElement.__mission3RendezvousState;
  const configKey = JSON.stringify([
    data.planet_name,
    data.planet_radius_au,
    data.target_angle_degrees,
    data.transfer_days,
  ]);
  if (state && state.configKey !== configKey) {
    if (state.raf !== null) cancelAnimationFrame(state.raf);
    parentElement.__mission3RendezvousState = null;
    root.innerHTML = '';
    delete root.dataset.ready;
    delete root.dataset.wired;
    state = null;
  }
  if (!state) {
    state = {
      angle: data.snapshot.angle,
      status: data.snapshot.status,
      progress: data.snapshot.progress,
      revision: data.snapshot.revision || 0,
      dragging: false,
      raf: null,
      lastTime: null,
      configKey,
    };
    parentElement.__mission3RendezvousState = state;
  } else if ((data.snapshot.revision || 0) > state.revision) {
    state.angle = data.snapshot.angle;
    state.status = data.snapshot.status;
    state.progress = data.snapshot.progress;
    state.revision = data.snapshot.revision;
  }
  state.data = data;

  const width = 640;
  const height = 520;
  const centerX = width / 2;
  const centerY = height / 2;
  const limit = data.planet_radius_au * 1.32;
  const scale = 205 / limit;
  const px = (x) => centerX + x * scale;
  const py = (y) => centerY - y * scale;
  const pathFromPoints = (points) => points.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${px(p[0]).toFixed(2)} ${py(p[1]).toFixed(2)}`
  ).join(' ');

  if (!root.dataset.ready) {
    root.innerHTML = `
      <div class="rendezvous-layout">
        <div class="rendezvous-plot">
          <svg viewBox="0 0 640 520" role="img" aria-label="태양 중심 전이 궤도 랑데부 시뮬레이션">
            <circle class="rendezvous-orbit" id="rendezvous-orbit"></circle>
            <path class="rendezvous-target" id="rendezvous-target"></path>
            <path class="rendezvous-transfer" id="rendezvous-transfer"></path>
            <circle class="rendezvous-sun" cx="320" cy="260" r="9"></circle>
            <circle class="rendezvous-earth" id="rendezvous-earth" r="6"></circle>
            <path class="rendezvous-transfer" id="rendezvous-trail" style="stroke:#50c8ff;stroke-width:2"></path>
            <circle class="rendezvous-ship" id="rendezvous-ship" r="7"></circle>
            <circle class="rendezvous-handle" id="rendezvous-planet" r="10" tabindex="0" role="slider"></circle>
            <text class="rendezvous-label" x="332" y="255">태양</text>
            <text class="rendezvous-label" id="rendezvous-earth-label"></text>
            <text class="rendezvous-label" id="rendezvous-planet-label"></text>
            <text class="rendezvous-label" id="rendezvous-ship-label"></text>
          </svg>
          <div class="rendezvous-controls">
            <button type="button" data-action="fine">미세 조정</button>
            <button type="button" data-action="align">계산된 위치로 맞추기</button>
            <button type="button" data-action="play">재생</button>
            <button type="button" data-action="pause">일시정지</button>
            <button type="button" data-action="reset">초기화</button>
          </div>
          <p class="rendezvous-note">행성을 공전 궤도 원 위에서 드래그할 수 있습니다. 각도는 지구 출발 방향(+x축)에서 반시계 방향으로 측정합니다.</p>
        </div>
        <aside class="rendezvous-stats">
          <h4>랑데부 계기판</h4>
          <p>계산된 위상각: <strong id="stat-target"></strong></p>
          <p>현재 행성 각도: <strong id="stat-angle"></strong></p>
          <p>목표 각도와 차이: <strong id="stat-error"></strong></p>
          <p>전이 시간: <strong id="stat-time"></strong></p>
          <p>우주선 위치: <strong id="stat-ship"></strong></p>
          <p>행성 위치: <strong id="stat-planet"></strong></p>
          <p>도착 거리: <strong id="stat-distance"></strong></p>
          <p>판정: <strong id="stat-status"></strong></p>
          <p id="stat-progress"></p>
        </aside>
      </div>`;
    root.dataset.ready = 'true';
  }

  const svg = root.querySelector('svg');
  const orbit = root.querySelector('#rendezvous-orbit');
  const targetLine = root.querySelector('#rendezvous-target');
  const transfer = root.querySelector('#rendezvous-transfer');
  const trail = root.querySelector('#rendezvous-trail');
  const ship = root.querySelector('#rendezvous-ship');
  const planet = root.querySelector('#rendezvous-planet');
  const earth = root.querySelector('#rendezvous-earth');
  const targetRad = data.target_angle_degrees * Math.PI / 180;
  const destinationRadius = data.planet_radius_au;
  orbit.setAttribute('cx', centerX);
  orbit.setAttribute('cy', centerY);
  orbit.setAttribute('r', destinationRadius * scale);
  targetLine.setAttribute('d', `M ${centerX} ${centerY} L ${px(destinationRadius * Math.cos(targetRad))} ${py(destinationRadius * Math.sin(targetRad))}`);
  transfer.setAttribute('d', pathFromPoints(data.transfer_path));
  earth.setAttribute('cx', px(1));
  earth.setAttribute('cy', py(0));
  root.querySelector('#rendezvous-earth-label').textContent = '지구 출발';

  const wrap = (degrees) => ((degrees % 360) + 360) % 360;
  const angleDelta = (target, current) => ((wrap(target) - wrap(current) + 180) % 360 + 360) % 360 - 180;
  const spacecraftAt = (progress) => {
    const scaled = Math.max(0, Math.min(1, progress)) * (data.spacecraft_path.length - 1);
    const index = Math.floor(scaled);
    const fraction = scaled - index;
    const a = data.spacecraft_path[index];
    const b = data.spacecraft_path[Math.min(index + 1, data.spacecraft_path.length - 1)];
    return [a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction];
  };
  const positionsAt = (progress) => {
    const [sx, sy] = spacecraftAt(progress);
    const days = data.transfer_days * progress;
    const radians = (state.angle + 360 * days / data.planet_period_days) * Math.PI / 180;
    return {
      ship: [sx, sy],
      planet: [destinationRadius * Math.cos(radians), destinationRadius * Math.sin(radians)],
      days,
    };
  };
  const updateDisplay = () => {
    const { ship: shipPos, planet: planetPos, days } = positionsAt(state.progress);
    ship.setAttribute('cx', px(shipPos[0]));
    ship.setAttribute('cy', py(shipPos[1]));
    planet.setAttribute('cx', px(planetPos[0]));
    planet.setAttribute('cy', py(planetPos[1]));
    planet.setAttribute('aria-valuenow', wrap(state.angle).toFixed(3));
    planet.setAttribute('aria-valuetext', `${data.planet_name} ${wrap(state.angle).toFixed(3)}도`);
    root.querySelector('#rendezvous-planet-label').setAttribute('x', px(planetPos[0]) + 12);
    root.querySelector('#rendezvous-planet-label').setAttribute('y', py(planetPos[1]) - 10);
    root.querySelector('#rendezvous-planet-label').textContent = data.planet_name;
    root.querySelector('#rendezvous-ship-label').setAttribute('x', px(shipPos[0]) + 12);
    root.querySelector('#rendezvous-ship-label').setAttribute('y', py(shipPos[1]) + 16);
    root.querySelector('#rendezvous-ship-label').textContent = '우주선';
    const trailPoints = data.spacecraft_path.slice(0, Math.max(1, Math.ceil(state.progress * (data.spacecraft_path.length - 1)) + 1));
    trail.setAttribute('d', pathFromPoints(trailPoints));
    root.querySelector('#stat-target').textContent = `${wrap(data.target_angle_degrees).toFixed(4)}°`;
    root.querySelector('#stat-angle').textContent = `${wrap(state.angle).toFixed(4)}°`;
    root.querySelector('#stat-error').textContent = `${angleDelta(data.target_angle_degrees, state.angle).toFixed(4)}°`;
    root.querySelector('#stat-time').textContent = `${days.toFixed(2)} / ${data.transfer_days.toFixed(2)}일`;
    root.querySelector('#stat-ship').textContent = `(${shipPos[0].toFixed(4)}, ${shipPos[1].toFixed(4)}) AU`;
    root.querySelector('#stat-planet').textContent = `(${planetPos[0].toFixed(4)}, ${planetPos[1].toFixed(4)}) AU · 경과 ${days.toFixed(2)}일`;
    const finalShip = data.spacecraft_path[data.spacecraft_path.length - 1];
    const finalDays = data.transfer_days;
    const finalAngle = (state.angle + 360 * finalDays / data.planet_period_days) * Math.PI / 180;
    const finalPlanet = [destinationRadius * Math.cos(finalAngle), destinationRadius * Math.sin(finalAngle)];
    const arrivalKm = Math.hypot(finalShip[0] - finalPlanet[0], finalShip[1] - finalPlanet[1]) * data.au_to_km;
    root.querySelector('#stat-distance').textContent = `${arrivalKm.toLocaleString(undefined, {maximumFractionDigits: 0})} km`;
    root.querySelector('#stat-status').textContent = state.status === 'completed'
      ? (arrivalKm <= data.tolerance_km ? '만남 성공' : '만남 실패')
      : state.status === 'playing' ? '이동 중' : state.status === 'paused' ? '일시정지' : '대기 중';
    root.querySelector('#stat-progress').textContent = `전이 진행률: ${(state.progress * 100).toFixed(1)}% · 성공 기준 ${data.tolerance_km.toLocaleString()} km 이내`;
  };
  const report = () => {
    state.revision += 1;
    setStateValue('snapshot', {
      angle: wrap(state.angle),
      status: state.status,
      progress: state.progress,
      revision: state.revision,
    });
  };
  const setAngle = (newAngle) => {
    state.angle = wrap(newAngle);
    if (state.status === 'playing' || state.status === 'completed') {
      state.status = 'ready';
      state.progress = 0;
    }
    updateDisplay();
    report();
  };
  const stopAnimation = () => {
    if (state.raf !== null) cancelAnimationFrame(state.raf);
    state.raf = null;
    state.lastTime = null;
  };
  const tick = (time) => {
    if (state.status !== 'playing') return;
    if (state.lastTime === null) state.lastTime = time - state.progress * data.animation_duration_ms;
    state.progress = Math.min(1, (time - state.lastTime) / data.animation_duration_ms);
    updateDisplay();
    if (state.progress >= 1) {
      state.status = 'completed';
      stopAnimation();
      updateDisplay();
      report();
      return;
    }
    state.raf = requestAnimationFrame(tick);
  };
  const start = () => {
    if (state.status === 'completed') state.progress = 0;
    state.status = 'playing';
    state.lastTime = null;
    report();
    stopAnimation();
    state.raf = requestAnimationFrame(tick);
    updateDisplay();
  };
  const pause = () => {
    if (state.status !== 'playing') return;
    stopAnimation();
    state.status = 'paused';
    report();
    updateDisplay();
  };
  const reset = () => {
    stopAnimation();
    state.progress = 0;
    state.status = 'ready';
    state.angle = wrap(data.target_angle_degrees);
    report();
    updateDisplay();
  };
  if (!root.dataset.wired) {
    root.querySelector('[data-action="fine"]').addEventListener('click', () => {
      const diff = angleDelta(data.target_angle_degrees, state.angle);
      setAngle(state.angle + Math.sign(diff) * Math.min(5, Math.abs(diff)));
    });
    root.querySelector('[data-action="align"]').addEventListener('click', () => setAngle(data.target_angle_degrees));
    root.querySelector('[data-action="play"]').addEventListener('click', start);
    root.querySelector('[data-action="pause"]').addEventListener('click', pause);
    root.querySelector('[data-action="reset"]').addEventListener('click', reset);
    const dragStart = (event) => {
      if (event.target !== planet || state.status === 'playing') return;
      state.dragging = true;
      planet.setPointerCapture(event.pointerId);
    };
    const dragMove = (event) => {
      if (!state.dragging) return;
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      const local = point.matrixTransform(svg.getScreenCTM().inverse());
      const angle = Math.atan2(centerY - local.y, local.x - centerX) * 180 / Math.PI;
      state.angle = wrap(angle);
      if (state.status === 'completed') {
        state.status = 'ready';
        state.progress = 0;
      }
      updateDisplay();
    };
    const dragEnd = (event) => {
      if (!state.dragging) return;
      state.dragging = false;
      if (planet.hasPointerCapture(event.pointerId)) planet.releasePointerCapture(event.pointerId);
      report();
    };
    planet.addEventListener('pointerdown', dragStart);
    svg.addEventListener('pointermove', dragMove);
    svg.addEventListener('pointerup', dragEnd);
    svg.addEventListener('pointercancel', dragEnd);
    planet.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') setAngle(state.angle - 1);
      if (event.key === 'ArrowRight' || event.key === 'ArrowUp') setAngle(state.angle + 1);
    });
    root.dataset.wired = 'true';
  }
  if (state.status === 'playing' && state.raf === null) {
    state.lastTime = null;
    state.raf = requestAnimationFrame(tick);
  } else if (state.status !== 'playing') {
    stopAnimation();
  }
  updateDisplay();
  return () => stopAnimation();
}
"""

mission3_rendezvous_component = st.components.v2.component(
    "mission3_rendezvous",
    html=HTML,
    css=CSS,
    js=JS,
)


def _persist_rendezvous_state() -> None:
    component_state = st.session_state.get(COMPONENT_KEY, {})
    snapshot = (
        component_state.get("snapshot")
        if isinstance(component_state, dict)
        else getattr(component_state, "snapshot", None)
    )
    if not isinstance(snapshot, dict):
        return
    st.session_state.m3_rendezvous_angle_degrees = float(snapshot["angle"])
    st.session_state.m3_rendezvous_status = str(snapshot["status"])
    st.session_state.m3_rendezvous_progress = float(snapshot["progress"])
    st.session_state.m3_rendezvous_revision = int(snapshot["revision"])


def _extract_simulation_data(
    planet: Planet,
    semi_major_axis_au: float,
    eccentricity: float,
    focus_distance_au: float,
    semi_minor_axis_au: float,
) -> tuple[list[list[float]], list[list[float]]]:
    figure = mission2_orbit_simulation(
        planet,
        semi_major_axis_au,
        eccentricity,
        focus_distance_au,
        semi_minor_axis_au,
    )
    transfer_trace = next(
        trace for trace in figure.data if trace.name == "호만 전이 궤도"
    )
    transfer_path = [
        [float(x), float(y)]
        for x, y in zip(transfer_trace.x, transfer_trace.y)
    ]
    spacecraft_trace_index = next(
        index
        for index, trace in enumerate(figure.data)
        if trace.name == "우주선 현재 위치"
    )
    spacecraft_path = []
    for frame in figure.frames:
        frame_trace_index = frame.traces.index(spacecraft_trace_index)
        trace = frame.data[frame_trace_index]
        spacecraft_path.append([float(trace.x[0]), float(trace.y[0])])
    return transfer_path, spacecraft_path


def render_rendezvous_simulation(
    planet: Planet,
    semi_major_axis_au: float,
    eccentricity: float,
    focus_distance_au: float,
    semi_minor_axis_au: float,
    transfer_days: float,
    target_angle_degrees: float,
) -> None:
    if not math.isfinite(transfer_days) or transfer_days <= 0:
        st.error("전이 시간은 0보다 큰 유한한 값이어야 합니다.")
        return
    target_angle = normalize_angle_degrees(target_angle_degrees)
    current_angle = float(
        st.session_state.get("m3_rendezvous_angle_degrees", target_angle)
    )
    transfer_path, spacecraft_path = _extract_simulation_data(
        planet,
        semi_major_axis_au,
        eccentricity,
        focus_distance_au,
        semi_minor_axis_au,
    )
    snapshot = {
        "angle": current_angle,
        "status": st.session_state.get("m3_rendezvous_status", "ready"),
        "progress": float(st.session_state.get("m3_rendezvous_progress", 0.0)),
        "revision": int(st.session_state.get("m3_rendezvous_revision", 0)),
    }
    data = {
        "planet_name": planet.name,
        "planet_radius_au": planet.orbit_radius_au,
        "planet_period_days": planet.orbital_period_days,
        "target_angle_degrees": target_angle,
        "transfer_days": transfer_days,
        "transfer_path": transfer_path,
        "spacecraft_path": spacecraft_path,
        "au_to_km": 149_597_870.7,
        "tolerance_km": RENDEZVOUS_TOLERANCE_KM,
        "animation_duration_ms": 12_000,
        "snapshot": snapshot,
    }
    state = mission3_rendezvous_component(
        key=COMPONENT_KEY,
        data=data,
        default={"snapshot": snapshot},
        on_snapshot_change=_persist_rendezvous_state,
        width="stretch",
        height="content",
    )
    result = getattr(state, "snapshot", None)
    if isinstance(result, dict):
        current_angle = float(result.get("angle", current_angle))
        st.session_state.m3_rendezvous_angle_degrees = current_angle
        st.session_state.m3_rendezvous_status = str(
            result.get("status", snapshot["status"])
        )
        st.session_state.m3_rendezvous_progress = float(
            result.get("progress", snapshot["progress"])
        )

    angle_error = shortest_angle_difference_degrees(target_angle, current_angle)
    st.caption(
        f"계산된 위상각: {target_angle:.4f}° · "
        f"현재 설정: {current_angle:.4f}° · "
        f"각도 차이: {angle_error:+.4f}° · "
        f"만남 판정 허용 오차: {RENDEZVOUS_TOLERANCE_KM:,.0f} km"
    )
