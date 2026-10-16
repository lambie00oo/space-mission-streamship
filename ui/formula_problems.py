import math
from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from logic.answer_checker import check_numeric_answer


@dataclass(frozen=True)
class FormulaInput:
    key: str
    label: str
    provided_value: float
    unit: str
    format: str = "%.6g"
    strictly_positive: bool = False


_FORMULA_INPUT = st.components.v2.component(
    "space_mission_formula_input",
    html='<div class="formula-inputs"></div>',
    css="""
        .formula-inputs {
            align-items: center;
            color: var(--st-text-color);
            display: flex;
            flex-wrap: wrap;
            font-size: 1.2rem;
            gap: 0.35rem;
            line-height: 2.5;
            overflow-x: auto;
            padding: 0.35rem 0;
        }
        .formula-inputs input {
            background: #e8f4ff;
            border: 1.5px solid #50c8ff;
            border-radius: 0.25rem;
            box-sizing: border-box;
            color: #071426;
            font: inherit;
            height: 2.15rem;
            line-height: normal;
            min-width: 6.5ch;
            padding: 0.1rem 0.25rem;
            text-align: center;
            width: 8ch;
        }
        .formula-inputs input:focus {
            outline: 2px solid var(--st-primary-color);
            outline-offset: 1px;
        }
        .formula-fraction {
            align-items: stretch;
            display: inline-flex;
            flex-direction: column;
            line-height: 1.35;
            text-align: center;
            vertical-align: middle;
        }
        .formula-numerator {
            border-bottom: 1px solid currentColor;
            padding: 0 0.25rem 0.1rem;
        }
        .formula-denominator {
            padding: 0.1rem 0.25rem 0;
        }
        .formula-radical {
            align-items: center;
            display: inline-flex;
            white-space: nowrap;
        }
        .formula-radicand {
            border-top: 1px solid currentColor;
            padding: 0.1rem 0.2rem 0;
        }
    """,
    js="""
        export default function (component) {
            const { data, parentElement, setStateValue } = component;
            const root = parentElement.querySelector(".formula-inputs");
            if (!root) return;

            const inputKeys = data.inputs.map((item) => item.key);
            const signature = JSON.stringify([data.layout, inputKeys]);
            if (root.dataset.signature !== signature) {
                root.innerHTML = data.layout;
                for (const item of data.inputs) {
                    const slots = root.querySelectorAll(
                        `[data-formula-slot="${item.key}"]`
                    );
                    for (const slot of slots) {
                        const input = document.createElement("input");
                        input.type = "number";
                        input.step = "any";
                        input.inputMode = "decimal";
                        input.autocomplete = "off";
                        input.setAttribute("aria-label", item.label);
                        input.dataset.formulaInput = item.key;
                        slot.replaceWith(input);
                    }
                }
                root.dataset.signature = signature;
            }

            const fields = root.querySelectorAll("input[data-formula-input]");
            const currentValues = data.values || {};
            for (const input of fields) {
                const nextValue = currentValues[input.dataset.formulaInput] ?? "";
                if (input.value !== String(nextValue)) input.value = nextValue;
                input.oninput = (event) => {
                    const values = {};
                    for (const field of fields) {
                        const fieldKey = field.dataset.formulaInput;
                        if (
                            !Object.hasOwn(values, fieldKey) ||
                            field === event.currentTarget
                        ) {
                            values[fieldKey] = field.value;
                        }
                    }
                    setStateValue("values", values);
                };
            }
        }
    """,
)


def render_formula_problem(
    *,
    key: str,
    title: str,
    formula: str,
    formula_layout: str,
    inputs: tuple[FormulaInput, ...],
    calculate: Callable[[dict[str, float]], float],
    expected: float,
    tolerance: float,
    result_label: str,
    result_unit: str,
    success_message: str,
    hints: tuple[str, ...],
    formula_description: str | None = None,
) -> bool:
    """Render reactive formula inputs and submit the calculated result for checking."""
    if key in st.session_state:
        success_message_key = f"{key}_success_message"
        if success_message_key in st.session_state:
            st.success(st.session_state.pop(success_message_key))
        return True

    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.latex(formula)
        if formula_description:
            st.markdown(formula_description)
        st.markdown("**필요한 값**")
        provided_values = "\n".join(
            f"- {item.label}: {item.format % item.provided_value} {item.unit}".rstrip()
            for item in inputs
        )
        st.markdown(provided_values)

        component_key = f"{key}_formula_input"
        component_state = st.session_state.get(component_key, {})
        raw_values = component_state.get("values", {})
        component_result = _FORMULA_INPUT(
            key=component_key,
            data={
                "layout": formula_layout,
                "inputs": [
                    {"key": item.key, "label": item.label}
                    for item in inputs
                ],
                "values": raw_values,
            },
            default={"values": raw_values},
            on_values_change=lambda: None,
        )
        raw_values = component_result.get("values", raw_values) or {}
        st.caption("수식의 빈칸을 채우면 계산 결과가 자동으로 갱신됩니다.")

        values: dict[str, float] = {}
        missing_values = [
            item for item in inputs
            if raw_values.get(item.key, "") in ("", None)
        ]
        for item in inputs:
            raw_value = raw_values.get(item.key, "")
            if raw_value not in ("", None):
                try:
                    values[item.key] = float(raw_value)
                except (TypeError, ValueError):
                    missing_values.append(item)

        calculated: float | None = None
        if missing_values:
            st.info("필수 입력값을 모두 채워 주세요.")
        else:
            try:
                if any(not math.isfinite(value) for value in values.values()):
                    raise ValueError("모든 입력값은 유한한 숫자여야 합니다.")
                for item in inputs:
                    if item.strictly_positive and values[item.key] <= 0:
                        raise ValueError(f"{item.label}은(는) 0보다 커야 합니다.")
                calculated = calculate(values)
                if not math.isfinite(calculated):
                    raise ValueError("계산 결과가 유효한 유한수가 아닙니다.")
                st.metric(result_label, f"{calculated:.10g} {result_unit}".strip())
            except (ValueError, ZeroDivisionError, OverflowError) as error:
                st.warning(f"계산할 수 없는 입력입니다: {error}")

        submitted = st.button(
            "정답 확인",
            key=f"{key}_check",
            disabled=calculated is None,
        )
        if submitted and calculated is not None:
            if check_numeric_answer(calculated, expected, tolerance):
                st.session_state[key] = expected
                st.session_state[f"{key}_success_message"] = success_message
                st.rerun()

            if hints:
                st.info("\n".join(hints))
            st.error("오답입니다. 값을 수정하고 다시 시도해 주세요.")
            return False

    return key in st.session_state
