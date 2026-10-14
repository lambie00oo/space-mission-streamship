import ast
import math


MAX_EXPRESSION_LENGTH = 256
MAX_POWER_EXPONENT = 10_000


def evaluate_expression(expression: str) -> float:
    """Evaluate a small arithmetic expression without executing Python code."""
    expression = expression.strip()
    if not expression:
        raise ValueError("수식을 입력해 주세요.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("수식이 너무 깁니다.")

    try:
        tree = ast.parse(expression.replace("^", "**"), mode="eval")
    except (SyntaxError, ValueError):
        raise ValueError("수식 형식을 확인해 주세요.") from None

    if sum(1 for _ in ast.walk(tree)) > 64:
        raise ValueError("수식이 너무 복잡합니다.")

    return _evaluate_node(tree.body)


def _evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        try:
            return _finite(float(node.value))
        except OverflowError:
            raise ValueError("입력한 숫자가 너무 커서 계산할 수 없습니다.") from None

    if isinstance(node, ast.Name) and node.id == "pi":
        return math.pi

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_node(node.operand)
        return _finite(value if isinstance(node.op, ast.UAdd) else -value)

    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)

        if isinstance(node.op, ast.Add):
            value = left + right
        elif isinstance(node.op, ast.Sub):
            value = left - right
        elif isinstance(node.op, ast.Mult):
            value = left * right
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("0으로 나눌 수 없습니다.")
            value = left / right
        elif isinstance(node.op, ast.Pow):
            if abs(right) > MAX_POWER_EXPONENT:
                raise ValueError("지수가 너무 커서 계산할 수 없습니다.")
            try:
                value = math.pow(left, right)
            except (OverflowError, ValueError):
                raise ValueError("거듭제곱 결과를 계산할 수 없습니다.") from None
        else:
            raise ValueError("허용되지 않는 연산자입니다.")
        return _finite(value)

    if isinstance(node, ast.Call):
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id != "sqrt"
            or len(node.args) != 1
            or node.keywords
        ):
            raise ValueError("sqrt(값) 형식만 사용할 수 있습니다.")
        radicand = _evaluate_node(node.args[0])
        if radicand < 0:
            raise ValueError("음수의 제곱근은 계산할 수 없습니다.")
        return _finite(math.sqrt(radicand))

    raise ValueError("숫자, 괄호, 기본 연산, ^, sqrt(), pi만 사용할 수 있습니다.")


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("유한한 숫자 결과만 표시할 수 있습니다.")
    return value


def format_result(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1e12 or abs(value) < 1e-6:
        return f"{value:.8e}"
    if value.is_integer():
        return str(int(value))
    return f"{value:.12g}"
