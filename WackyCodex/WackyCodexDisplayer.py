import WackyCodex.WackyCodex as WackyCodex
from WackyCodex.WackyCodex import Object
import math
import random

def look(objects_seen: list[Object], player: Object) -> str:
    description_list = [
        f'**{obj.definition}**<multiplicity_of_object>{
            '\n- '+', '.join(WackyCodex.format_counted(WackyCodex.count_and_deduplicate(obj.inventory))) if obj.inventory else ''
        }' for obj in objects_seen
    ]
    description_list = WackyCodex.format_counted_special(WackyCodex.count_and_deduplicate(description_list), '<multiplicity_of_object>')
    message = '\n'.join(description_list)
    return message

def draw(objects_seen: list[Object], player: Object) -> str:
    display = []
    empty_symbol = '. '
    for i in range(15):
        display.append([])
        for j in range(15):
            display[i].append([])
    tags = ' 23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
    symbols_used = {}
    def find_symbol(char, objs):
        for tag in tags:
            if char + tag in symbols_used:
                compare_objs = symbols_used[char + tag]
                if WackyCodex.hash_object_list(compare_objs) == WackyCodex.hash_object_list(objs):
                    return char + tag
            else:
                symbols_used[char + tag] = objs
                return char + tag
        return char + '*'
    for obj in objects_seen:
        delta = obj.position - player.position
        clamped = delta.clamped(7)
        if math.isnan(clamped.x) or math.isnan(clamped.y) or math.isnan(clamped.z):
            continue
        display[int(-clamped.y)+7][int(clamped.x)+7].append(obj)
    for i, row in enumerate(display):
        for j, cell in enumerate(row):
            if len(cell) == 0:
                display[i][j] = empty_symbol
                continue
            if len(cell) == 1:
                obj = cell[0]
                symbol = find_symbol(obj.definition[0], [obj])
                display[i][j] = symbol
                continue
            if len(cell) >= 2:
                objs = cell
                symbol = find_symbol('+', objs)
                display[i][j] = symbol
                continue
    legend_lines = []
    max_legend_width = 70
    for symbol, objs in symbols_used.items():
        legend_pair = f'{symbol.strip()} = {" and ".join([f'{obj.definition}{(f" ({', '.join(obj.inventory)})") if obj.inventory else ''}' for obj in objs])}  '
        if not legend_lines:
            legend_lines.append(legend_pair)
            continue
        if len(legend_lines[-1] + legend_pair) > max_legend_width:
            legend_lines.append(legend_pair)
        else:
            legend_lines[-1] = legend_lines[-1] + legend_pair
    legend = '\n'.join(legend_lines)
    message = f'```\n{'\n'.join([''.join(line) for line in display])}\n\n{legend}```'
    return message

def scan(objects_seen: list[Object], player: Object) -> str:
    description_list = [
        f'**{obj.definition}** at {obj.position.str_numbers()} <multiplicity_of_object>{
            '\n- '+', '.join(WackyCodex.format_counted(WackyCodex.count_and_deduplicate(obj.inventory))) if obj.inventory else ''
        }' for obj in objects_seen
    ]
    description_list = WackyCodex.format_counted_special(WackyCodex.count_and_deduplicate(description_list), '<multiplicity_of_object>')
    message = '\n'.join(description_list)
    return message

def draw_ansi(objects_seen: list[Object], player: Object) -> str:
    display = []
    empty_symbol = '. '
    for i in range(15):
        display.append([])
        for j in range(15):
            display[i].append([])
    tags = [f'\u001b[{number}m' for number in (list(range(31, 38)) + list(range(41, 48)))]
    symbols_used = {}
    def find_symbol(char, objs: list[Object]):
        random.seed(objs[0].definition)
        free_symbols = []
        shuffled_tags = tags.copy()
        random.shuffle(shuffled_tags)
        for tag in shuffled_tags:
            symbol = tag + char + '\u001b[0m' + ' '
            if symbol in symbols_used:
                compare_objs = symbols_used[symbol]
                if WackyCodex.hash_object_list(compare_objs) == WackyCodex.hash_object_list(objs):
                    return symbol
            else:
                free_symbols.append(symbol)
                symbols_used[symbol] = objs
                return symbol
        if free_symbols:
            return random.choice(free_symbols)
        return char
    for obj in objects_seen:
        delta = obj.position - player.position
        clamped = delta.clamped(7)
        if math.isnan(clamped.x) or math.isnan(clamped.y) or math.isnan(clamped.z):
            continue
        display[int(-clamped.y)+7][int(clamped.x)+7].append(obj)
    for i, row in enumerate(display):
        for j, cell in enumerate(row):
            if len(cell) == 0:
                display[i][j] = empty_symbol
                continue
            if len(cell) == 1:
                obj = cell[0]
                symbol = find_symbol(obj.definition[0], [obj])
                display[i][j] = symbol
                continue
            if len(cell) >= 2:
                objs = cell
                symbol = find_symbol('+', objs)
                display[i][j] = symbol
                continue
    legend_lines = []
    max_legend_width = 70
    for symbol, objs in symbols_used.items():
        legend_pair = f'{symbol.strip()} = {" and ".join([f'{obj.definition}{(f" ({', '.join(obj.inventory)})") if obj.inventory else ''}' for obj in objs])}  '
        if not legend_lines:
            legend_lines.append(legend_pair)
            continue
        if len(legend_lines[-1] + legend_pair) > max_legend_width:
            legend_lines.append(legend_pair)
        else:
            legend_lines[-1] = legend_lines[-1] + legend_pair
    legend = '\n'.join(legend_lines)
    message = f'```ansi\n{'\n'.join([''.join(line) for line in display])}\n\n{legend}```'
    return message

def display_from_preference(objects_seen: list[Object], player: Object, preference: str) -> str:
    if preference == 'l':
        return look(objects_seen, player)
    elif preference == 'd':
        return draw(objects_seen, player)
    elif preference == 'a':
        return draw_ansi(objects_seen, player)
    elif preference == 's':
        return scan(objects_seen, player)
    return ''

