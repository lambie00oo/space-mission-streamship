import re

import streamlit as st

from logic.scientific_calculator import evaluate_expression, format_result


KEY_ROWS = (
    (("AC", "clear"), ("DEL", "delete"), ("(", "open"), (")", "close")),
    (("7", "7"), ("8", "8"), ("9", "9"), ("÷", "divide")),
    (("4", "4"), ("5", "5"), ("6", "6"), ("×", "multiply")),
    (("1", "1"), ("2", "2"), ("3", "3"), ("−", "subtract")),
    (("+/−", "sign"), ("0", "0"), (".", "decimal"), ("+", "add")),
    (("x²", "square"), ("x³", "cube"), ("xʸ", "power"), ("π", "pi")),
    (("√x", "sqrt"), ("1/x", "reciprocal"), ("%", "percent"), ("EE", "exponent")),
)


def _ends_with_value(expression: str) -> bool:
    stripped = expression.rstrip()
    return stripped.endswith(")") or stripped.endswith("pi") or (
        bool(stripped) and (stripped[-1].isdigit() or stripped[-1] == ".")
    )


def _append_token(expression: str, token: str) -> str:
    expression = expression.rstrip()
    if token == "pi":
        return f"{expression}*pi" if _ends_with_value(expression) else f"{expression}pi"
    if token == "(" and _ends_with_value(expression):
        return f"{expression}*("
    if token.isdigit() and _ends_with_value(expression) and (
        expression.endswith(")") or expression.endswith("pi")
    ):
        return f"{expression}*{token}"
    if token == ".":
        last_number = re.search(
            r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d*)?$",
            expression,
        )
        if last_number:
            mantissa = re.split("[eE]", last_number.group())[0]
            if "." in mantissa or "e" in last_number.group().lower():
                return expression
        elif not expression or expression[-1] in "+-*/^(":
            return f"{expression}0."
        elif _ends_with_value(expression):
            return f"{expression}*0."
    return f"{expression}{token}"


def _handle_key(action: str) -> None:
    expression = st.session_state.get("calculator_expression", "")

    if action == "clear":
        expression = ""
    elif action == "delete":
        expression = expression[:-1]
    elif action == "sign":
        if not expression:
            expression = "-"
        elif expression.startswith("-(") and expression.endswith(")"):
            expression = expression[2:-1]
        else:
            expression = f"-({expression})"
    elif action in ("square", "cube", "sqrt", "reciprocal", "percent"):
        if expression or action == "sqrt":
            if action == "square":
                expression = f"({expression})^2"
            elif action == "cube":
                expression = f"({expression})^3"
            elif action == "sqrt":
                expression = f"sqrt({expression})" if expression else "sqrt("
            elif action == "reciprocal":
                expression = f"1/({expression})"
            else:
                expression = f"({expression})/100"
    elif action == "exponent":
        if expression and (expression[-1].isdigit() or expression[-1] == "."):
            expression += "e"
    else:
        token_by_action = {
            "open": "(",
            "close": ")",
            "divide": "/",
            "multiply": "*",
            "subtract": "-",
            "add": "+",
            "power": "^",
            "pi": "pi",
            "decimal": ".",
        }
        token = token_by_action.get(action, action)
        if token == ")" and expression.count("(") <= expression.count(")"):
            return
        if token in ("+", "-", "*", "/", "^") and expression.endswith(
            ("+", "-", "*", "/", "^")
        ):
            expression = expression[:-1] + token
        else:
            expression = _append_token(expression, token)

    st.session_state.calculator_expression = expression
    st.session_state.pop("calculator_error", None)


def _calculate() -> None:
    expression = st.session_state.get("calculator_expression", "").strip()
    try:
        result = evaluate_expression(expression)
    except (ValueError, ZeroDivisionError) as error:
        st.session_state.calculator_error = str(error)
        st.session_state.pop("calculator_result_expression", None)
        st.session_state.pop("calculator_result", None)
        return

    result_text = format_result(result)
    st.session_state.calculator_result_expression = expression
    st.session_state.calculator_result = result_text
    st.session_state.pop("calculator_error", None)
    history = st.session_state.setdefault("calculator_history", [])
    history.insert(0, {"expression": expression, "result": result_text})


def _clear_history() -> None:
    st.session_state.calculator_history = []


def render_calculator() -> None:
    with st.container(key="calculator-sticky-panel"):
        with st.container(key="calculator-scroll-content"):
            st.subheader("공학용 계산기")
            st.caption("수식 입력 · ^는 거듭제곱, pi는 π, EE는 10의 지수 표기입니다.")
            st.text_input(
                "현재 수식",
                key="calculator_expression",
                placeholder="예: sqrt(1.262^3)/2",
            )

            for row_index, row in enumerate(KEY_ROWS):
                columns = st.columns(4, gap="small")
                for column, (label, action) in zip(columns, row):
                    with column:
                        st.button(
                            label,
                            key=f"calculator_key_{row_index}_{action}",
                            on_click=_handle_key,
                            args=(action,),
                            use_container_width=True,
                        )

            st.button(
                "=",
                key="calculator_equals",
                on_click=_calculate,
                use_container_width=True,
            )

            expression = st.session_state.get("calculator_expression", "").strip()
            st.markdown("**계산 결과**")
            if st.session_state.get("calculator_error"):
                st.error(st.session_state.calculator_error)
            elif (
                expression
                and st.session_state.get("calculator_result_expression") == expression
            ):
                st.success(st.session_state.calculator_result)
            else:
                st.caption("수식을 입력하고 = 를 눌러 계산하세요.")

            st.divider()
            st.markdown("**계산 기록**")
            history = st.session_state.setdefault("calculator_history", [])
            st.button(
                "기록 전체 지우기",
                key="calculator_clear_history",
                on_click=_clear_history,
                use_container_width=True,
            )
            if not history:
                st.caption("아직 계산 기록이 없습니다.")
                return

            for item in history:
                st.markdown(f"`{item['expression']}`")
                st.caption(f"결과: `{item['result']}`")
