"""Read-only selection bounds derived from the stored device recipe list."""
import ast
from pathlib import Path

source = Path(__file__).parents[1] / 'braumeister_bridge/app/bridge.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'control_screen')
method.decorator_list = []
namespace = {}
exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), namespace)
parse = namespace['control_screen']


def test_nine_recipes_with_status_field_one():
    recipes = 'header\n' + '\n'.join('X'.join([str(i)] + ['0'] * 19) + f'.Recipe {i};' for i in range(9))
    for slot in range(9):
        fields = ['0'] * 16
        fields[3], fields[8], fields[9], fields[14] = '2015', '1', str(slot), 'ph'
        payload = 'FW;TEST;1;' + 'X'.join(fields)
        assert parse(payload, recipes) == ('2015', 'ph', str(slot), '9')
        assert parse(payload)[3] == '1'
        fields[3] = '101'
        assert parse('FW;TEST;1;' + 'X'.join(fields), recipes)[3] == '1'


def test_noncontiguous_list_does_not_override_count():
    fields = ['0'] * 16
    fields[3], fields[8] = '2015', '1'
    line = 'X'.join(['3'] + ['0'] * 19) + '.Invalid gap;'
    assert parse('FW;TEST;1;' + 'X'.join(fields), line)[3] == '1'
