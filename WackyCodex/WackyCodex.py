
from dataclasses import dataclass
import random
from typing import Any, Callable, Generator, Iterable, TypeAlias
from math import sqrt, nan, inf, isnan, isinf
import re
import difflib

current_version = 1

def clamp(num, minimum, maximum):
    return min(max(num, minimum), maximum)

def sign(num):
    if num > 0:
        return 1
    if num < 0:
        return -1
    if num == 0:
        return 0
    return nan

def subfinitize(num):
    if isinf(num):
        return sign(num)
    elif isnan(num):
        return num
    else:
        return 0

def finish(generator):
    try:
        next(generator)
    except StopIteration as stop:
        return stop.value
    
def send_and_finish(generator, send_value):
    try:
        generator.send(send_value)
    except StopIteration as stop:
        return stop.value
    
def count_and_deduplicate(the_list: list[Any]) -> list[tuple[Any, int]]:
    if not the_list:
        return []
    new_list = []
    count = 0
    previous_elem = the_list[0]
    for elem in the_list:
        if elem == previous_elem:
            count += 1
        else:
            new_list.append((previous_elem, count))
            previous_elem = elem
            count = 1
    new_list.append((previous_elem, count))
    return new_list

def format_as_multiplicity(number) -> str:
    if number == 1:
        return ''
    return f' (x{number})'

def format_counted(the_list):
    return (f'{x[0]}{format_as_multiplicity(x[1])}' for x in the_list)

def format_counted_special(the_list, string_replacement):
    return (f'{str(x[0]).replace(string_replacement, format_as_multiplicity(x[1]), 1)}' for x in the_list)

class Vector:
    x: float
    y: float
    z: float
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: 'Vector'):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scale: float):
        return Vector(self.x * scale, self.y * scale, self.z * scale)
    
    def __rmul__(self, scale: float):
        return self * scale
    
    def __sub__(self, other: 'Vector'):
        return self + (-1 * other)
    
    def __truediv__(self, scale: float):
        return self * (1/scale)
    
    def __eq__(self, __value) -> bool:
        return isinstance(__value, Vector) and self.x == __value.x and self.y == __value.y and self.z == __value.z
    
    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))
    
    def magnitude(self):
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def distance(self, other: 'Vector'):
        return (self - other).magnitude()
    
    def rounded(self, digits=0):
        return Vector(round(self.x, digits), round(self.y, digits), round(self.z, digits))
    
    def normalized(self):
        if self.is_zero():
            return self
        finitized = self.finitize()
        return finitized / finitized.magnitude()
    
    def clamped(self, max_per_axis):
        return Vector(clamp(self.x, -max_per_axis, max_per_axis), clamp(self.y, -max_per_axis, max_per_axis), clamp(self.z, -max_per_axis, max_per_axis))
    
    def is_zero(self):
        return self.x == 0 and self.y == 0 and self.z == 0

    def is_nan(self):
        return isnan(self.x) or isnan(self.y) or isnan(self.z)
    
    def is_inf(self):
        return isinf(self.x) or isinf(self.y) or isinf(self.z)
    
    def finitize(self):
        if not self.is_inf():
            return self
        return Vector(subfinitize(self.x), subfinitize(self.y), subfinitize(self.z))
    
    def copy(self):
        return Vector(self.x, self.y, self.z)
    
    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y}, {self.z})"
    
    def str_numbers(self) -> str:
        return f'({self.x}, {self.y}, {self.z})'.replace('.0', '')

    def describe_axis(self, list, value, pos: str, neg: str, omit_zero=True, zero: str = '', signify=False, units='') -> None:
        if abs(value % 1) <= 0.001 or abs(value % 1) >= 0.999:
            value = int(value)
        return_str = pos if value > 0 else neg if value < 0 else '' if omit_zero else zero
        if signify:
            value = f'+{value}' if value > 0 else f'-{value}' if value < 0 else f'{value}' if value == 0 else 'nan'
        else:
            value = abs(value)
        return_str = f'{value}{f' {units}' if units else ''} {return_str}' if return_str else ''
        if return_str:
            list.append(return_str)

    def describe_relative(self, style='cardinal', units:str|None=None, zero_vector:str='Nowhere') -> str:
        units = ' ' + units if units else ''
        axis_descriptions = []
        if style == 'cardinal':
            self.describe_axis(axis_descriptions, self.x, 'east', 'west', units=units)
            self.describe_axis(axis_descriptions, self.y, 'north', 'south', units=units)
            self.describe_axis(axis_descriptions, self.z, 'up', 'down', units=units)
        if style == 'vague':
            self.describe_axis(axis_descriptions, self.x, 'over', 'over', units=units)
            self.describe_axis(axis_descriptions, self.y, 'up', 'down', units=units)
            self.describe_axis(axis_descriptions, self.z, 'out', 'in', units=units)
        if style == 'exact':
            units = units.strip() + ' ' if units else units
            self.describe_axis(axis_descriptions, self.x, f'{units}X', f'{units}X', False, f'{units}X', True)
            self.describe_axis(axis_descriptions, self.y, f'{units}Y', f'{units}Y', False, f'{units}Y', True)
            self.describe_axis(axis_descriptions, self.z, f'{units}Z', f'{units}Z', False, f'{units}Z', True)
        return ', '.join(axis_descriptions) or zero_vector
    
    @staticmethod
    def zero() -> 'Vector':
        return Vector(0, 0, 0)

class Ctx:
    verbs: dict[str, 'Verb']
    object_definitions: dict[str, 'ObjectDefinition']
    objects: list['Object']
    myself: 'Object'
    this: 'Object'
    that: 'Object'
    these: list['Object']
    those: list['Object']
    other: 'Object'
    range: float
    stop: bool
    skip: bool
    owner_lookup: dict[str, 'Owner']
    output_lines: list[str]
    muted: bool
    vector_describing_mode: str
    vector_describing_units: str|None
    objects_with_owners: list['Object']
    focused_owner: 'Owner'
    ctx_created_from: str
    operations_performed: int
    operations_performed_total: int
    maximum_performable_operations: int
    version: int
    groups: dict[str, 'Group']
    passive_ticks: int
    def __init__(self) -> None:
        self.verbs = {}
        self.object_definitions = {}
        self.objects = []
        self.myself = NULL_OBJECT
        self.this = NULL_OBJECT
        self.that = NULL_OBJECT
        self.these = []
        self.those = []
        self.other = NULL_OBJECT
        self.range = 15
        self.stop = False
        self.skip = False
        self.owner_lookup = {}
        self.output_lines = []
        self.muted = False
        self.vector_describing_mode = 'cardinal'
        self.vector_describing_units = None
        self.objects_with_owners = []
        self.focused_owner = NULL_OWNER
        self.ctx_created_from = 'System'
        self.operations_performed = 0
        self.operations_performed_total = 0
        self.maximum_performable_operations = 400
        self.version = current_version
        self.groups = {}
        self.passive_ticks = 0
        # EACH TIME YOU SEE THIS: do you need to increase the version?
        # TODO: Loader module
    def set_missing_defaults(self):
        compare = Ctx()
        assigned = []
        for attr in compare.__dict__:
            if not hasattr(self, attr):
                setattr(self, attr, getattr(compare, attr))
                assigned.append(attr)
        return assigned
    def set_this(self, value):
        self.that = self.this
        self.this = value
    def set_these(self, value):
        self.those = self.these
        self.these = value
    def reset_execution(self):
        self.skip, self.stop = False, False
        self.operations_performed = 0
    def look_for_objects(self) -> Iterable['Object']:
        for obj in self.objects:
            interaction_radius = self.object_definitions[obj.definition].interaction_radius
            if self.myself.position.distance(obj.position) <= interaction_radius or interaction_radius == inf:
                yield obj
    def look_for_objects_at_position(self, position: Vector) -> Iterable['Object']:
        return (obj for obj in self.objects if obj.position == position)
    def lookup_definition_or_null(self, word:str):
        return self.object_definitions.get(word, NULL_OBJECT_DEFINITION)
    def get_definition_or_null_of(self, obj: 'Object'):
        return self.object_definitions.get(obj.definition, NULL_OBJECT_DEFINITION)

    def focus(self, owner: str):
        self.focused_owner = self.owner_lookup.setdefault(owner, Owner(owner))
        return self.focused_owner

    # World Interface
    def spawn(self, name: str, position: Vector, set_to_this=False, output_creation=False, successful_creation_callback=None, failed_creation_callback=None, start_of_execution=False) -> 'Object':
        if start_of_execution:
            self.reset_execution()
        definition = NULL_OBJECT_DEFINITION
        try:
            definition: 'ObjectDefinition' = self.object_definitions[name]
        except KeyError:
            if failed_creation_callback:
                failed_creation_callback()
            else:
                self.error(f"Failed to spawn {name}, since it doesn't have a definition yet!")
                return NULL_OBJECT
        new_object = Object(name)
        new_object.inventory = definition.default_inventory.copy()
        new_object.AI = definition.AI
        new_object.position = position.copy()
        self.objects.append(new_object)
        if definition.owner:
            self.owner_lookup.setdefault(definition.owner, Owner(definition.owner, new_object)).primary_object = new_object
            self.objects_with_owners.append(new_object)
        if set_to_this:
            self.set_this(new_object)
        if output_creation:
            self.output(new_object, 'was spawned', source_object=new_object)
        if successful_creation_callback:
            successful_creation_callback(new_object)
        new_object.run_procedure(definition.initialize_procedure, new_object, new_object, self)
        return new_object
    
    def despawn(self, obj: 'Object'):
        try:
            self.objects.remove(obj)
        except ValueError:
            self.error('The game tried to despawn', obj, ',', 'but they were already deleted. This is an error.', source_object=obj)
        if self.myself == obj:
            self.myself = NULL_OBJECT
        if self.other == obj:
            self.other = NULL_OBJECT
        if self.this == obj:
            self.this = NULL_OBJECT
        if self.that == obj:
            self.that = NULL_OBJECT
        try:
            self.these.remove(obj)
        except ValueError:
            pass
        try:
            self.those.remove(obj)
        except ValueError:
            pass
        for owner in self.owner_lookup.values():
            if owner.primary_object == obj:
                owner.primary_object = NULL_OBJECT
        try:
            self.objects_with_owners.remove(obj)
        except ValueError:
            pass
        obj.destroyed = True
        self.output(obj, 'was destroyed!', source_object=obj)

    def null_if_destroyed(self, obj: 'Object') -> 'Object':
        return NULL_OBJECT if obj.destroyed else obj
    
    def scrub_stack(self, stack: tuple['Object',...]) -> tuple['Object',...]:
        return tuple(self.null_if_destroyed(obj) for obj in stack)
    
    def search_for_owned_object(self, owner: str) -> 'Object':
        for obj in self.objects:
            if definition := self.get_definition_or_null_of(obj):
                if definition.owner == owner:
                    return obj
        raise LookupError(f'Object with owner "{owner}" was not found', 'player-missing')

    def get_object_by_owner(self, owner: str) -> 'Object':
        return self.owner_lookup.setdefault(owner, Owner(owner)).get_object_or_set(self.search_for_owned_object(owner))

    def control_owned_object(self, owner: str, verb: str, other_name: str|None = None):
        self.reset_execution()
        self.myself = self.get_object_by_owner(owner)
        self.other = self.myself
        if other_name:
            self.other = ObjectReferenceName(other_name).get(ctx=self)
            if self.other == NULL_OBJECT:
                raise LookupError(f'A(n) "{other_name}" was not found to act upon')
        self.myself.do(verb, self.other, ctx=self)

    def look_around_as_owned_object(self, owner: str) -> list['Object']:
        myself = self.get_object_by_owner(owner)
        stack = (self.myself,)
        (self.myself,) = (myself,)
        objects_seen = list(self.look_for_objects())
        for obj in objects_seen:
            self.output(obj, solo=True)
        (self.myself,) = self.scrub_stack(stack)
        return objects_seen

    def output_line(self, line):
        self.output_lines.append(line)

    def output_to_players(self, line, source_object:'Object|None'=None, only_for:'None|list[Object]'=None, force=False, spheres:None|tuple[tuple[Vector, float], ...]=None):
        source_object = source_object or self.myself
        spheres = spheres or ((source_object.position, source_object.get_radius(self)),)
        #radius = self.get_definition_or_null_of(self.myself).interaction_radius
        for owner_obj in self.objects_with_owners:
            owner: Owner = self.owner_lookup[self.get_definition_or_null_of(owner_obj).owner]
            if owner.developer_mode or force or (any(sphere[0].distance(owner_obj.position) <= sphere[1] for sphere in spheres) and (only_for is None or owner.primary_object in only_for)):
                owner.output_lines.append(line)

    def output(self, *args: 'str|Object|Verb|Group|tuple[str,str]|list[Object]', source_object=None, spheres:None|tuple[tuple[Vector, float], ...]=None, force=False, solo=False, only_for:'None|list[Object]'=None, never_space=False):
        if self.muted and not force:
            return
        line = ''
        no_next_space = False
        no_space = False
        for arg in args:
            append = ''
            if isinstance(arg, str):
                left_lookup = {'<left-single-quote>': '\'', '<left-double-quote>': '"'}
                right_lookup = {'<right-single-quote>': '\'', '<right-double-quote>': '"'}
                if arg in ['.', ',', '!', '?']:
                    no_space = True
                if arg in left_lookup:
                    no_next_space = True
                    arg = left_lookup[arg]
                if arg in right_lookup:
                    no_space = True
                    arg = right_lookup[arg]
                append = arg
            elif isinstance(arg, Object):
                append = f'**{arg.definition}**'
            elif isinstance(arg, Verb):
                append = f'*{arg.name}*'
            elif isinstance(arg, Group):
                append = f'**{arg.name}**'
            elif isinstance(arg, tuple) and len(arg) == 2:
                if arg[0] == 'Object':
                    append = f'**{arg[1]}**'
                if arg[0] == 'Verb':
                    append = f'*{arg[1]}*'
            elif isinstance(arg, list):
                if len(arg) == 0:
                    append = 'nothing'
                if len(arg) == 1:
                    append = f'**{arg[0].definition}**'
                if len(arg) == 2:
                    append = f'**{arg[0].definition}** and **{arg[1].definition}**' # no comma
                if len(arg) > 2:
                    append = f'{', '.join((f'**{obj.definition}**' for obj in arg[:-1]))}and **{arg[-1].definition}**'
            else:
                append = str(arg)
            line += f'{append}' if no_space or never_space else f' {append}'
            no_space = no_next_space
            no_next_space = False
        line = line.lstrip()
        self.output_line(line)
        if not solo or force:
            self.output_to_players(line, source_object=source_object, spheres=spheres, only_for=only_for, force=force)

    def error(self, *args: 'str|Object|Verb|tuple[str,str]|list[Object]', source_object=None, spheres=None):
        self.output(*args, force=True, source_object=source_object, spheres=spheres)

    def clear_output(self):
        self.output_lines.clear()

    def read_and_clear_output(self) -> str:
        output = format_counted(count_and_deduplicate(self.output_lines))
        output = '\n'.join(output)
        self.clear_output()
        return output

    def compile_and_prompt(self, text: str, auto_confirm=False, permit_place=False):
        '''Yields a list of diffs. Use `.send(confirm: bool)` to approve or deny the changes'''
        new_obj_defs, new_verbs, new_groups, warnings = compile(text, self, False, permit_place=permit_place)
        diffs = []
        for new_obj_def in new_obj_defs:
            diffs.append(self.diff(self.lookup_definition_or_null(new_obj_def.name).source, new_obj_def.source))
        for new_verb in new_verbs:
            diffs.append(self.diff(self.verbs.get(new_verb.name, NULL_VERB).source, new_verb.source))
        for new_group in new_groups:
            diffs.append(self.diff(self.groups.get(new_group.name, NULL_GROUP).source, new_group.source))
        confirm = auto_confirm
        if not auto_confirm:
            confirm = yield diffs, warnings
        if confirm:
            for new_obj_def in new_obj_defs:
                self.object_definitions[new_obj_def.name] = new_obj_def
            for new_verb in new_verbs:
                self.verbs[new_verb.name] = new_verb
            for new_group in new_groups:
                self.groups[new_group.name] = new_group
        return True

    def diff(self, old:str, new: str) -> str:
        old_lines = old.splitlines()
        new_lines = new.splitlines()
        msg = ''
        for line in difflib.unified_diff(old_lines, new_lines, 'before', 'after', n=100):
            if line.startswith('@@'):
                continue
            msg += line + '\n'
        return msg
    
    def create_player(self, player_name: str, player_id: str):
        compilation = self.compile_and_prompt(f'OBJECT\nNAME: {player_name}\nAI: PLAYER\nOWNER: {player_id}')
        confirm = yield next(compilation)
        send_and_finish(compilation, confirm)
        player_object = self.spawn(player_name, Vector.zero(), False)

    def lookup(self, word, concat=False) -> str:
        obj_def = self.lookup_definition_or_null(word).source
        verb_def = self.verbs.get(word, NULL_VERB).source
        group_def = self.groups.get(word, NULL_GROUP).source
        if not obj_def and not verb_def and not group_def:
            return 'That word is not defined yet.'
        if not concat:
            obj_def = f'```\n{obj_def}\n```\n' if obj_def else obj_def
            verb_def = f'```\n{verb_def}\n```' if verb_def else verb_def
            group_def = f'```\n{group_def}\n```' if group_def else group_def
            return obj_def + verb_def + group_def
        else:
            return f'```{obj_def}\n\n{verb_def}\n\n{group_def}```'
    
    def lookup_all(self) -> str:
        msg = ''
        for obj_def in self.object_definitions.values():
            msg += obj_def.source + '\n'
        for verb_def in self.verbs.values():
            msg += verb_def.source + '\n'
        for group_def in self.groups.values():
            msg += group_def.source + '\n'
        return msg
    
    def spill(self, word) -> str:
        obj_def = self.lookup_definition_or_null(word)
        verb_def = self.verbs.get(word, NULL_VERB)
        group_def = self.groups.get(word, NULL_GROUP)
        if not obj_def and not verb_def and not group_def:
            return 'That word is not defined yet.'
        obj_def = f'\n{obj_def}\n\n' if obj_def else obj_def
        verb_def = f'\n{verb_def}\n' if verb_def else verb_def
        group_def = f'\n{group_def}\n' if group_def else group_def
        return obj_def + verb_def
    
    def before_move(self, start_position, new_position):
        for obj in self.look_for_objects_at_position(new_position):
            procedure = self.object_definitions[obj.definition].before_moved_into_procedure
            if procedure is not NULL_PROCEDURE:
                obj.run_procedure(procedure, obj, self.myself, self)
        for obj in self.look_for_objects_at_position(start_position):
            procedure = self.object_definitions[obj.definition].before_moved_out_of_procedure
            if procedure is not NULL_PROCEDURE:
                obj.run_procedure(procedure, obj, self.myself, self)

    def after_move(self, start_position, new_position):
        for obj in self.look_for_objects_at_position(new_position):
            procedure = self.object_definitions[obj.definition].when_moved_into_procedure
            if procedure is not NULL_PROCEDURE:
                obj.run_procedure(procedure, obj, self.myself, self)
        for obj in self.look_for_objects_at_position(start_position):
            procedure = self.object_definitions[obj.definition].when_moved_out_of_procedure
            if procedure is not NULL_PROCEDURE:
                obj.run_procedure(procedure, obj, self.myself, self)
    
    def execute_AI_action(self, obj: 'Object', action: str):
        if (match := re.findall(r'^(.+?) (.+)$', action)):
            verb = match[0][0]
            recieving_object_reference = compile_object_reference(match[0][1])
            recieving_objects = recieving_object_reference.get_all(self)
            for recieving_obj in recieving_objects:
                obj.do(verb, recieving_obj, self)
        elif (match := re.findall(r'^(.+)$', action)):
            verb = match[0]
            obj.do(verb, obj, self)

    def tick(self, passive_tick=False):
        for obj in self.objects:
            object_definition = self.get_definition_or_null_of(obj)
            if object_definition.AI == AI_NONE:
                continue
            if object_definition.AI == AI_PLAYER:
                continue
            if not object_definition.actions:
                continue
            self.reset_execution()
            self.myself = obj
            if object_definition.AI == AI_RANDOM:
                action = random.choice(object_definition.actions)
                self.execute_AI_action(obj, action)
            if object_definition.AI == AI_SEQUENCE:
                obj.action_cursor = (obj.action_cursor + 1) % len(object_definition.actions)
                action = object_definition.actions[obj.action_cursor]
                self.execute_AI_action(obj, action)
            if object_definition.AI == AI_REVERSE:
                obj.action_cursor = (obj.action_cursor - 1) % len(object_definition.actions)
                action = object_definition.actions[obj.action_cursor]
                self.execute_AI_action(obj, action)
        if passive_tick:
            self.passive_ticks += 1
        else:
            self.passive_ticks = 0

    # TODO: Other world interface methods
    # TODO: Figure out time
    # TODO: Disallow reassigning OWNER of an definition to an id that isn't yours

@dataclass(repr=False)
class Opcode:
    def exec(self, ctx: Ctx):
        raise NotImplementedError("This opcode is not implemented!")
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        pass
    
    def __repr__(self) -> str:
        return f"{(self.__class__.__name__)} - {repr(self.__dict__)}"
    
class _OpNoop(Opcode):
    def exec(self, ctx: Ctx):
        pass

OpNoop = _OpNoop()


class Procedure:
    opcodes: list[Opcode]

    def __init__(self) -> None:
        self.opcodes = []

    def exec(self, ctx: Ctx):
        for opcode in self.opcodes:
            if (ctx.skip):
                ctx.skip = False
                continue
            if (ctx.operations_performed > ctx.maximum_performable_operations):
                ctx.stop = True
                break
            opcode.exec(ctx)
            ctx.operations_performed += 1
            ctx.operations_performed_total += 1
            if (ctx.stop):
                break
            if (ctx.operations_performed > ctx.maximum_performable_operations):
                ctx.error(f'A maximum of {ctx.maximum_performable_operations} operations has been hit! An infinite loop probably occurred. Or you\'re trying to do something incredibly complex.')
                ctx.stop = True
                break

    def __repr__(self) -> str:
        return repr(self.opcodes)

NULL_PROCEDURE = Procedure()

class Verb:
    def __init__(self) -> None:    
        self.name = 'unnamed-verb'
        self.tenses: dict[str, str] = {}
        self.procedure: Procedure = NULL_PROCEDURE
        self.source = ''
        # If you add anything here, you will need to increase the version.
    
    # <simple>, <plural>, <present>, <past>, <future>

    def simple(self):
        return ('Verb', self.tenses['simple'])
    
    def plural(self):
        return ('Verb', self.tenses['plural'])
    
    def present(self):
        return ('Verb', self.tenses['present continuous'])
    
    def past(self):
        return ('Verb', self.tenses['past'])
    
    def future(self):
        return ('Verb', self.tenses['future'])
    
    def __repr__(self) -> str:
        return repr(self.__dict__)

NULL_VERB = Verb()
    

AI_NONE = 0
AI_RANDOM = 1
AI_SEQUENCE = 2
AI_REVERSE = 3
AI_PLAYER = 4

AI_LOOKUP_DICTIONARY =  {
    'NONE': AI_NONE,
    'RANDOM': AI_RANDOM,
    'SEQUENCE': AI_SEQUENCE,
    'REVERSE': AI_REVERSE,
    'PLAYER': AI_PLAYER
}

def parse_AI(string: str, line=None) -> int:
    try:
        return AI_LOOKUP_DICTIONARY[string.upper()]
    except KeyError:
        raise CompilationError(line, 'AI Type', f'Invalid, unsupported, or misspelled AI type. Valid AI types are {list(AI_LOOKUP_DICTIONARY.keys())}', substring=string)

class ObjectDefinition:
    def __init__(self) -> None:
        self.name = 'Unnamed-Object'
        self.default_inventory = []
        #self.position = Vector(0, 0, 0)
        self.actions = []
        self.AI: int = AI_NONE
        self.owner = ''
        self.initialize_procedure: Procedure = NULL_PROCEDURE
        self.before_perform_action_procedures: dict[str, Procedure] = {}
        self.before_receive_action_procedures: dict[str, Procedure] = {}
        self.when_perform_action_procedures: dict[str, Procedure] = {}
        self.when_receive_action_procedures: dict[str, Procedure] = {}
        self.before_moved_into_procedure: Procedure = NULL_PROCEDURE
        self.before_moved_out_of_procedure: Procedure = NULL_PROCEDURE
        self.when_moved_into_procedure: Procedure = NULL_PROCEDURE
        self.when_moved_out_of_procedure: Procedure = NULL_PROCEDURE
        self.source = ''
        self.interaction_radius = 15.0

    def __repr__(self) -> str:
        the_dict = self.__dict__.copy()
        the_dict.pop('source')
        return repr(the_dict)

NULL_OBJECT_DEFINITION = ObjectDefinition()

class Object:
    def __init__(self, name='Unnamed-Object') -> None:
        self.definition: str = name
        self.inventory: list[str] = []
        self.position: Vector = Vector(0, 0, 0)
        self.AI: int|None = None
        self.action_cursor = 0
        self.destroyed = False
        # If you add anything here, you will need to increase the version.

    def add_item(self, item: str):
        self.inventory.append(item)
        self.inventory.sort()

    def add_items(self, items: Iterable[str]):
        for item in items:
            self.inventory.append(item)
        self.inventory.sort()

    def get_radius(self, ctx: Ctx) -> float:
        return ctx.get_definition_or_null_of(self).interaction_radius
    
    def get_sphere(self, ctx: Ctx) -> tuple[Vector, float]:
        return (self.position, self.get_radius(ctx))

    def do(self, verb_name: str, other: 'Object', ctx: Ctx, silent=False):
        try:
            object_definition: ObjectDefinition = ctx.object_definitions[self.definition]
        except KeyError:
            ctx.error(self, f'tried to {verb_name}, but... is not a defined entity. THEY AREN\'T REAL!!', source_object=ctx.myself)
            return
        try:
            other_definition: ObjectDefinition = ctx.object_definitions[other.definition]
        except KeyError:
            ctx.error(self, f'tried to {verb_name}', other, ',', 'but... that is not a defined entity. THEY AREN\'T REAL!!', source_object=ctx.myself)
            return
        try:
            verb: Verb = ctx.verbs[verb_name]
        except KeyError:
            ctx.error(self, f'tried to {verb_name}, but that\'s not a word in the dictionary yet.', source_object=ctx.myself)
            return
        # setup
        stack = (ctx.myself, ctx.other)
        # my before
        (ctx.myself, ctx.other) = ctx.scrub_stack((self, other or self))
        if not silent:
            ctx.output(self, ctx.verbs[verb_name].past(), other, source_object=ctx.myself, spheres=(ctx.myself.get_sphere(ctx), ctx.other.get_sphere(ctx)))
        object_definition.before_perform_action_procedures.get(verb_name, NULL_PROCEDURE).exec(ctx)
        # other before
        (ctx.myself, ctx.other) = ctx.scrub_stack((other or self, self))
        other_definition.before_receive_action_procedures.get(verb_name, NULL_PROCEDURE).exec(ctx)
        # verb
        (ctx.myself, ctx.other) = ctx.scrub_stack((self, other or self))
        verb.procedure.exec(ctx)
        # my when
        (ctx.myself, ctx.other) = ctx.scrub_stack((self, other or self))
        object_definition.when_perform_action_procedures.get(verb_name, NULL_PROCEDURE).exec(ctx)
        # other when
        (ctx.myself, ctx.other) = ctx.scrub_stack((other or self, self))
        other_definition.when_receive_action_procedures.get(verb_name, NULL_PROCEDURE).exec(ctx)
        # end
        (ctx.myself, ctx.other) = ctx.scrub_stack(stack)

    def run_procedure(self, procedure: Procedure, myself, other, ctx: Ctx):
        stack = (ctx.myself, ctx.other)
        (ctx.myself, ctx.other) = ctx.scrub_stack((myself or self, other or myself or self))
        procedure.exec(ctx)
        (ctx.myself, ctx.other) = ctx.scrub_stack(stack)

    def equals(self, __value: object) -> bool:
        return (
            isinstance(__value, Object) and
            self.definition == __value.definition and 
            self.inventory == __value.inventory and
            #self.position == __value.position and
            self.AI == __value.AI
        )
    
    def __hash__(self) -> int:
        return hash((
            hash(self.definition),
            hash(tuple(self.inventory)),
            hash(self.position),
            hash(self.AI),
        ))
    
    def hash_aspatial(self) -> int:
        return hash((
            hash(self.definition),
            hash(tuple(self.inventory)),
            hash(self.AI),
        ))
    
def hash_object_list(objs: list[Object]) -> int:
    return hash(tuple((obj.hash_aspatial() for obj in objs)))

NULL_OBJECT = Object()
NULL_OBJECT.definition = 'Missing-Object'
NULL_OBJECT.position = Vector(nan, nan, nan)

def FIND_NEAREST_OBJECT(objects: Iterable, relative_to: Object, ctx: Ctx) -> Object:
    objects = list(objects)
    if not objects:
        return NULL_OBJECT
    def _compare_by_distance(obj: Object):
        return relative_to.position.distance(obj.position)
    return min(objects, key=_compare_by_distance)

@dataclass(repr=False)
class ObjectReference():
    def get(self, ctx: Ctx) -> Object:
        return NULL_OBJECT
    
    def get_all(self, ctx: Ctx) -> list[Object]:
        return [self.get(ctx)]
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
    
@dataclass(repr=False, kw_only=True)
class Predicate():
    negated: bool=False
    def eval(self, ctx: Ctx) -> bool:
        return self.eval_inner(ctx) != self.negated
    
    def eval_inner(self, ctx: Ctx) -> bool: # override this one
        return True
    
    def eval_given_object(self, obj: Object, ctx: Ctx) -> bool:
        return self.eval(ctx)
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        pass
    
    def __repr__(self) -> str:
        return f"{(self.__class__.__name__)} - {repr(self.__dict__)}"
    
class PredicateTrue(Predicate):
    def eval_inner(self, ctx: Ctx) -> bool:
        return True
    
class PredicateFalse(Predicate):
    def eveval_inneral(self, ctx: Ctx) -> bool:
        return False
    
class PredicateMaybe(Predicate):
    def eveval_inneral(self, ctx: Ctx) -> bool:
        return random.random() > 0.5
    
NULL_PREDICATE = PredicateFalse()

@dataclass(repr=False)
class PredicateObject(Predicate):
    obj_ref: ObjectReference
    def eval_inner(self, ctx: Ctx) -> bool:
        objs = self.obj_ref.get_all(ctx)
        return bool(objs) and not (len(objs) == 1 and objs[0] is NULL_OBJECT)
    
    def eval_given_object(self, obj: Object, ctx: Ctx) -> bool:
        return self.eval_given_object_inner(obj, ctx) != self.negated
    
    def eval_given_object_inner(self, obj: Object, ctx: Ctx) -> bool: # override this one
        return obj != NULL_OBJECT
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        if isinstance(self.obj_ref, ObjectReferenceName):
            self.obj_ref.check_for_warnings(ctx, line, warning_list)
    
@dataclass(repr=False)
class PredicateObjectHas(PredicateObject):
    item: str
    def eval_inner(self, ctx: Ctx) -> bool:
        items = [self.item]
        if self.item.startswith('#') and (group_name := self.item[1:]) in ctx.groups:
            items = ctx.groups[group_name].items
        for obj in self.obj_ref.get_all(ctx):
            for item in items:
                if item in obj.inventory:
                    return True
        return False
    
    def eval_given_object_inner(self, obj: Object, ctx: Ctx) -> bool:
        return self.item in obj.inventory
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        super().check_for_warnings(ctx, line, warning_list)
        if any(keyword in self.item for keyword in keywords_set):
            warning_list.append(CompilationWarning(line, 'Predicate', f'This may not have compiled as you expected. This part is looking for objects with an item "{self.item}", which contains a keyword.\n{decoration}', substring=self.item))

@dataclass(repr=False) 
class PredicateObjectIsA(PredicateObject):
    name: str
    def eval_inner(self, ctx: Ctx) -> bool:
        for obj in self.obj_ref.get_all(ctx):
            if obj.definition == self.name:
                return True
        return False
    
    def eval_given_object_inner(self, obj: Object, ctx: Ctx) -> bool:
        return obj.definition == self.name
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        super().check_for_warnings(ctx, line, warning_list)
        if any(keyword in self.name for keyword in keywords_set):
            warning_list.append(CompilationWarning(line, 'Predicate', f'This may not have compiled as you expected. This part is looking for objects with the name "{self.name}", which contains a keyword.\n{decoration}', substring=self.name))

@dataclass(repr=False) 
class PredicateObjectIs(PredicateObject):
    match_obj_ref: ObjectReference
    def eval_inner(self, ctx: Ctx) -> bool:
        objs = self.obj_ref.get_all(ctx)
        match_objs = self.match_obj_ref.get_all(ctx)
        if len(objs) != len(match_objs):
            return False
        for obj in objs:
            if obj not in match_objs:
                return False
        for match_obj in match_objs:
            if match_obj not in objs:
                return False
        return True
    
    def eval_given_object_inner(self, obj: Object, ctx: Ctx) -> bool:
        match_objs = self.match_obj_ref.get_all(ctx)
        if len(match_objs) != 1:
            return False
        return obj == match_objs[0]
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        super().check_for_warnings(ctx, line, warning_list)
        if isinstance(self.match_obj_ref, ObjectReferenceName):
            self.match_obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)    
class PredicateObjectIsIn(PredicateObject):
    match_obj_ref: ObjectReference
    def eval_inner(self, ctx: Ctx) -> bool:
        objs = self.obj_ref.get_all(ctx)
        match_objs = self.match_obj_ref.get_all(ctx)
        for obj in objs:
            if obj in match_objs:
                return True
        return False
    
    def eval_given_object_inner(self, obj: Object, ctx: Ctx) -> bool:
        match_objs = self.match_obj_ref.get_all(ctx)
        return obj in match_objs
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list, decoration=''):
        super().check_for_warnings(ctx, line, warning_list)
        if isinstance(self.match_obj_ref, ObjectReferenceName):
            self.match_obj_ref.check_for_warnings(ctx, line, warning_list)

def IS_OBJECT_IN_RANGE(obj: Object, range: float, ctx: Ctx) -> bool:
    return ctx.myself.position.distance(obj.position) <= range

def IS_OBJECT_A(obj: Object, name: str) -> bool:
    return obj.definition == name

def IS_OBJECT(obj: Object, other_obj: Object) -> bool:
    return obj == other_obj

def IS_OBJECT_ONE_OF(obj: Object, other_objs: list[Object]) -> bool:
    return obj in other_objs

def DOES_OBJECT_HAVE(obj: Object, item: str) -> bool:
    return item in obj.inventory

def FIND_OBJECTS_IN_RANGE(objects: Iterable[Object], range: float, ctx: Ctx) -> Iterable[Object]:
    return filter(lambda obj: IS_OBJECT_IN_RANGE(obj, range, ctx), objects)

def FIND_INTERACTABLE_OBJECTS(objects: Iterable[Object], ctx: Ctx) -> Iterable[Object]:
    return filter(lambda obj: IS_OBJECT_IN_RANGE(obj, ctx.get_definition_or_null_of(obj).interaction_radius, ctx), objects)

def FIND_OBJECTS_MATCHING_PREDICATE(objects: Iterable[Object], predicate: Callable[[Object], bool]) -> Iterable[Object]:
    return filter(lambda obj: predicate(obj), objects)

class Selector():
    def select_one(self, objects: Iterable[Object], ctx: Ctx) -> Object:
        raise RuntimeError('Invalid singular selector')
    
    def select_multiple(self, objects: Iterable[Object], ctx: Ctx) -> list[Object]:
        raise RuntimeError('Invalid multiple selector')
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'
    
class SelectorNull(Selector):
    def select_one(self, objects: Iterable[Object], ctx: Ctx) -> Object:
        return NULL_OBJECT
    
    def select_multiple(self, objects: Iterable[Object], ctx: Ctx) -> list[Object]:
        return []
    
NULL_SELECTOR = SelectorNull()
    
class SelectorRandom(Selector):
    def select_one(self, objects: Iterable[Object], ctx: Ctx) -> Object:
        objs = list(objects)
        if not objs:
            return NULL_OBJECT
        return random.choice(objs)
    
class SelectorNearest(Selector):
    def select_one(self, objects: Iterable[Object], ctx: Ctx) -> Object:
        objs = list(objects)
        if not objs:
            return NULL_OBJECT
        return min(objs, key=lambda obj: ctx.myself.position.distance(obj.position))
    
class SelectorFarthest(Selector):
    def select_one(self, objects: Iterable[Object], ctx: Ctx) -> Object:
        objs = list(objects)
        if not objs:
            return NULL_OBJECT
        return max(objs, key=lambda obj: ctx.myself.position.distance(obj.position))
    
class SelectorAll(Selector):
    def select_multiple(self, objects: Iterable[Object], ctx: Ctx) -> list[Object]:
        return list(objects)
    
class ObjectReferenceNull(ObjectReference):
    def get_all(self, ctx: Ctx) -> list[Object]:
        return []
    
NULL_OBJECT_REFERENCE = ObjectReferenceNull()

class ObjectReferenceMyself(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        return ctx.myself
    
class ObjectReferenceOther(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        return ctx.other
    
class ObjectReferenceThis(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        return ctx.this
    
class ObjectReferenceThat(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        return ctx.that
    
class ObjectReferenceGroup(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        raise RuntimeError("Improper use of group targeting as single target")

    def get_all(self, ctx: Ctx) -> list[Object]:
        return []

class ObjectReferenceThese(ObjectReferenceGroup):
    def get_all(self, ctx: Ctx) -> list[Object]:
        return ctx.these
    
class ObjectReferenceThose(ObjectReferenceGroup):
    def get_all(self, ctx: Ctx) -> list[Object]:
        return ctx.those
    
class ObjectReferenceAll(ObjectReferenceGroup):
    def get_all(self, ctx: Ctx) -> list[Object]:
        return list(ctx.look_for_objects())
    
class ObjectReferenceSomething(ObjectReference):
    def get(self, ctx: Ctx) -> Object:
        return SelectorRandom().select_one(FIND_INTERACTABLE_OBJECTS(ctx.objects, ctx), ctx)

@dataclass(repr=False)
class ObjectReferenceName(ObjectReference):
    name: str
    def get(self, ctx: Ctx) -> Object:
        nearest_found = FIND_NEAREST_OBJECT(FIND_OBJECTS_MATCHING_PREDICATE(FIND_INTERACTABLE_OBJECTS(ctx.objects, ctx), lambda obj: IS_OBJECT_A(obj, self.name)), ctx.myself, ctx)
        if not nearest_found:
            return NULL_OBJECT
        return nearest_found
    
    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if self.name not in ctx.object_definitions:
            warning_list.append(CompilationWarning(line, 'Object Reference', f'{self.name} is neither a keyword and also isn\'t the name of a definition. It should be one of the following: {object_reference_keywords_list} or a name of an object definition with 1 or more characters', substring=self.name))
        if any(keyword in self.name for keyword in keywords_set):
            warning_list.append(CompilationWarning(line, 'Object Reference', f'This may not have compiled as you expected. This part is looking for objects with the name "{self.name}", which contains a keyword.', substring=self.name))
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} - {self.name}>"

@dataclass(repr=False)
class OpCreate(Opcode):
    definition: str
    def exec(self, ctx: Ctx):
        def successful_creation_callback(new_object: Object):
            ctx.output(ctx.myself, 'created', new_object, '.', spheres=(ctx.myself.get_sphere(ctx), new_object.get_sphere(ctx)))
        ctx.spawn(self.definition, ctx.myself.position, 
                  set_to_this=True, 
                  successful_creation_callback=successful_creation_callback,
                  failed_creation_callback=lambda:ctx.error(ctx.myself, 'tried to create', self.definition, ',', "but couldn't since there is no definition for it yet.")
        )

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if not self.definition in ctx.object_definitions:
            warning_list.append(CompilationWarning(line, 'Code', f'{self.definition} is not a defined object.', substring=self.definition))

@dataclass(repr=False)
class OpFind(Opcode):
    obj_ref_from: ObjectReference
    selector: Selector
    find_multiple: bool
    predicate: Predicate
    def exec(self, ctx: Ctx):
        if self.find_multiple:
            ctx.set_these(self.selector.select_multiple(filter(lambda obj: self.predicate.eval_given_object(obj, ctx), self.obj_ref_from.get_all(ctx)), ctx))
        else:
            ctx.set_this(self.selector.select_one(filter(lambda obj: self.predicate.eval_given_object(obj, ctx), self.obj_ref_from.get_all(ctx)), ctx))

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if isinstance(self.obj_ref_from, ObjectReferenceName):
            self.obj_ref_from.check_for_warnings(ctx, line, warning_list)
        self.predicate.check_for_warnings(ctx, line, warning_list, decoration=self.dissect())

    def dissect(self) -> str:
        dissected_selector = self.selector.__class__.__name__.removeprefix('Selector').lower()
        if dissected_selector != 'all':
            dissected_selector = 'the ' + dissected_selector
        dissected_return_type = 'objects' if self.find_multiple else 'object'
        dissected_obj_ref_from = self.obj_ref_from.__class__.__name__.removeprefix('ObjectReference').lower()
        if isinstance(self.obj_ref_from, ObjectReferenceAll):
            dissected_obj_ref_from = f'{dissected_obj_ref_from} availible'
        if isinstance(self.obj_ref_from, ObjectReferenceName):
            dissected_obj_ref_from = f'the nearest object with the name "{self.obj_ref_from.name}"'
        elif isinstance(self.obj_ref_from, ObjectReferenceGroup):
            dissected_obj_ref_from = f'{dissected_obj_ref_from} objects'
        else:
            dissected_obj_ref_from = f'{dissected_obj_ref_from} object'
        dissected_predicate = ''
        if isinstance(self.predicate, PredicateObjectHas):
            dissected_predicate = f'have the item "{self.predicate.item}"'
        elif isinstance(self.predicate, PredicateObjectIsA):
            dissected_predicate = f'have the name "{self.predicate.name}"'
        elif isinstance(self.predicate, PredicateObjectIs):
            if isinstance(self.predicate.match_obj_ref, ObjectReferenceName):
                dissected_predicate = f'are specifically the nearest object that is named "{self.predicate.match_obj_ref.name}"'
            else:
                dissected_predicate = f'are specifically "{self.predicate.match_obj_ref.__class__.__name__.removeprefix('ObjectReference').upper()}"'
        elif isinstance(self.predicate, PredicateObjectIsIn):
            if isinstance(self.predicate.match_obj_ref, ObjectReferenceName):
                dissected_predicate = f'are one of the objects in the set of the nearest object that is named "{self.predicate.match_obj_ref.name}"'
            else:
                dissected_predicate = f'are one of the objects in the set of "{self.predicate.match_obj_ref.__class__.__name__.removeprefix('ObjectReference').upper()}"'
        return f'This is how the FIND statement was interpreted:\nFind {dissected_selector} {dissected_return_type} searching from the set of {dissected_obj_ref_from} for objects that {dissected_predicate}.'

@dataclass(repr=False)
class OpGive(Opcode):
    obj_ref: ObjectReference
    item: str
    def exec(self, ctx: Ctx):
        for obj in self.obj_ref.get_all(ctx):
            if self.item.startswith('#') and self.item[1:] in ctx.groups:
                group = ctx.groups[self.item[1:]]
                ctx.output(ctx.myself, 'gave', group, 'to', obj, '.', source_object=ctx.myself, spheres=(ctx.myself.get_sphere(ctx), obj.get_sphere(ctx)))
                obj.add_items(group.items)
            else:
                ctx.output(ctx.myself, 'gave', self.item, 'to', obj, '.', source_object=ctx.myself, spheres=(ctx.myself.get_sphere(ctx), obj.get_sphere(ctx)))
                obj.add_item(self.item)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if isinstance(self.obj_ref, ObjectReferenceName):
            self.obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpRemove(Opcode):
    obj_ref: ObjectReference
    item: str
    def exec(self, ctx: Ctx):
        if self.item.startswith('#') and self.item[1:] in ctx.groups:
            group = ctx.groups[self.item[1:]]
            for obj in self.obj_ref.get_all(ctx):
                for remove_item in group.items:
                    try:
                        obj.inventory.remove(remove_item)
                    except ValueError:
                        pass
                ctx.output(ctx.myself, 'removed', group, 'from', obj, '.', source_object=ctx.myself, spheres=(ctx.myself.get_sphere(ctx), obj.get_sphere(ctx)))
        else:
            for obj in self.obj_ref.get_all(ctx):
                try:
                    obj.inventory.remove(self.item)
                    ctx.output(ctx.myself, 'removed', self.item, 'from', obj, '.', source_object=ctx.myself, spheres=(ctx.myself.get_sphere(ctx), obj.get_sphere(ctx)))
                except ValueError:
                    ctx.output(ctx.myself, 'tried to remove', self.item, 'from', obj, ',', 'but there wasn\'t anything to take.')

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if isinstance(self.obj_ref, ObjectReferenceName):
            self.obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpMove(Opcode):
    movement: Vector
    def exec(self, ctx: Ctx):
        start_position = ctx.myself.position
        radius = ctx.myself.get_radius(ctx)
        start_sphere =  (start_position, radius)
        new_position = ctx.myself.position + self.movement
        new_position = new_position.rounded()
        new_sphere = (new_position, radius)
        ctx.before_move(start_position, new_position)
        if ctx.stop:
            return
        ctx.myself.position = new_position
        ctx.output(ctx.myself, f'moved {self.movement.describe_relative(ctx.vector_describing_mode, ctx.vector_describing_units, 'nowhere')}.', spheres=(start_sphere, new_sphere))
        ctx.after_move(start_position, new_position)

@dataclass(repr=False)
class OpGoTo(Opcode):
    destination: Vector
    def exec(self, ctx: Ctx):
        start_position = ctx.myself.position
        radius = ctx.myself.get_radius(ctx)
        start_sphere =  (start_position, radius)
        new_position = self.destination.copy()
        new_position = new_position.rounded()
        new_sphere = (new_position, radius)
        ctx.before_move(start_position, new_position)
        if ctx.stop:
            return
        ctx.myself.position = new_position
        ctx.output(ctx.myself, 'teleported!', spheres=(start_sphere, new_sphere))
        ctx.after_move(start_position, new_position)

@dataclass(repr=False)
class OpBringTowards(Opcode):
    moving_obj_ref: ObjectReference
    target_obj_ref: ObjectReference
    def exec(self, ctx: Ctx):
        moving_objects: list[Object] = self.moving_obj_ref.get_all(ctx)
        target_objects: list[Object] = self.target_obj_ref.get_all(ctx)
        if not target_objects:
            if moving_objects:
                ctx.output(moving_objects, 'tried to move towards something but couldn\'t find anything to move towards.', source_object=moving_objects[0])
            return
        for obj in moving_objects:
            target_object = FIND_NEAREST_OBJECT(target_objects, obj, ctx)
            start_position = obj.position
            radius = ctx.myself.get_radius(ctx)
            start_sphere =  (start_position, radius)
            new_position = obj.position + (target_object.position - obj.position).normalized()
            new_position = new_position.rounded()
            new_sphere = (new_position, radius)
            ctx.before_move(start_position, new_position)
            if ctx.stop:
                return
            obj.position = new_position
            ctx.output(obj, 'moved towards', target_object, '.', source_object=obj, spheres=(start_sphere, new_sphere))
            ctx.after_move(start_position, new_position)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        for obj_ref in (self.moving_obj_ref, self.target_obj_ref):
            if isinstance(obj_ref, ObjectReferenceName):
                obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpBringTo(Opcode):
    moving_obj_ref: ObjectReference
    target_obj_ref: ObjectReference
    def exec(self, ctx: Ctx):
        moving_objects: list[Object] = self.moving_obj_ref.get_all(ctx)
        target_objects: list[Object] = self.target_obj_ref.get_all(ctx)
        if not target_objects:
            if moving_objects:
                ctx.output(moving_objects, 'tried to teleport to something but couldn\'t find anything to teleport to.', source_object=moving_objects[0])
            return
        for obj in moving_objects:
            target_object = FIND_NEAREST_OBJECT(target_objects, obj, ctx)
            start_position = obj.position
            radius = ctx.myself.get_radius(ctx)
            start_sphere =  (start_position, radius)
            new_position = target_object.position.copy()
            new_position = new_position.rounded()
            new_sphere = (new_position, radius)
            ctx.before_move(start_position, new_position)
            if ctx.stop:
                return
            obj.position = new_position
            ctx.output(obj, 'teleported to', target_object, '.', source_object=obj, spheres=(start_sphere, new_sphere))
            ctx.after_move(start_position, new_position)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        for obj_ref in (self.moving_obj_ref, self.target_obj_ref):
            if isinstance(obj_ref, ObjectReferenceName):
                obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpDo(Opcode):
    verb_name: str
    verb_other: ObjectReference
    def exec(self, ctx: Ctx):
        other_objects = self.verb_other.get_all(ctx) or [ctx.myself]
        for other in other_objects:
            ctx.myself.do(self.verb_name, other, ctx)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if self.verb_name not in ctx.verbs:
            CompilationWarning(line, 'Code', f'{self.verb_name} is not a defined verb.', substring=self.verb_name)
        if isinstance(self.verb_other, ObjectReferenceName):
            self.verb_other.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpTell(Opcode):
    silent: bool
    told_object: ObjectReference
    verb_name: str
    verb_other: ObjectReference
    def exec(self, ctx: Ctx):
        other_objects = self.verb_other.get_all(ctx) or 'itself!'
        for obj in self.told_object.get_all(ctx):
            if other_objects == 'itself!':
                obj.do(self.verb_name, obj, ctx, silent=self.silent)
            else:
                for other in other_objects:
                    obj.do(self.verb_name, other, ctx, silent=self.silent)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if self.verb_name not in ctx.verbs:
            CompilationWarning(line, 'Code', f'{self.verb_name} is not a defined verb.', substring=self.verb_name)
        for obj_ref in (self.told_object, self.verb_other):
            if isinstance(obj_ref, ObjectReferenceName):
                obj_ref.check_for_warnings(ctx, line, warning_list)

class OpStop(Opcode):
    def exec(self, ctx: Ctx):
        ctx.output('The action was interrupted.')
        ctx.stop = True

@dataclass(repr=False)
class OpDestroy(Opcode):
    obj_ref: ObjectReference
    def exec(self, ctx: Ctx):
        for obj in self.obj_ref.get_all(ctx):
            ctx.despawn(obj)

    def check_for_warnings(self, ctx: Ctx, line, warning_list: list):
        if isinstance(self.obj_ref, ObjectReferenceName):
            self.obj_ref.check_for_warnings(ctx, line, warning_list)

@dataclass(repr=False)
class OpAnd(Opcode):
    operation_1: Opcode
    operation_2: Opcode
    def exec(self, ctx: Ctx):
        self.operation_1.exec(ctx)
        self.operation_2.exec(ctx)

@dataclass(repr=False)
class OpIf(Opcode):
    predicate: Predicate
    negated: bool=False
    def exec(self, ctx: Ctx):
        if not (self.predicate.eval(ctx) != self.negated):
            ctx.skip = True

@dataclass(repr=False)
class OpPick(Opcode):
    obj_ref: ObjectReference
    def exec(self, ctx: Ctx):
        objs = self.obj_ref.get_all(ctx)
        if not objs:
            ctx.set_this(NULL_OBJECT)
        ctx.set_this(random.choice(objs))

@dataclass(repr=False)
class OpOutput(Opcode):
    stuff: list[ObjectReference|str]
    @staticmethod 
    def resolve(stuff: list[ObjectReference|str], ctx: Ctx):
        for thing in stuff:
            if isinstance(thing, ObjectReference):
                yield list(thing.get_all(ctx))
            else:
                yield thing

    def exec(self, ctx: Ctx):
        resolved = list(self.resolve(self.stuff, ctx))
        ctx.output(*resolved, never_space=True)

@dataclass(repr=False)
class OpRawOutput(Opcode):
    string: str
    def exec(self, ctx: Ctx):
        ctx.output(self.string, never_space=True)

@dataclass(repr=False)
class OpOutputTo(OpOutput):
    recipient: ObjectReference
    def exec(self, ctx: Ctx):
        resolved = list(self.resolve(self.stuff, ctx))
        ctx.output(*resolved, only_for=self.recipient.get_all(ctx), never_space=True)

@dataclass(repr=False)
class OpRawOutputTo(OpRawOutput):
    recipient: ObjectReference
    def exec(self, ctx: Ctx):
        ctx.output(self.string, only_for=self.recipient.get_all(ctx), never_space=True)

class OpMute(Opcode):
    def exec(self, ctx: Ctx):
        ctx.muted = True

class OpUnmute(Opcode):
    def exec(self, ctx: Ctx):
        ctx.muted = False

class OpUnstop(Opcode):
    def exec(self, ctx: Ctx):
        ctx.stop = False

class Group():
    name: str
    items: list
    source: str
    def __init__(self):
        self.name = 'Unnamed Group'
        self.items = []
        self.source = ''
        # If you add anything here, you will need to increase the version.

    def __contains__(self, item):
        return item in self.items
    
    def __repr__(self) -> str:
        return f'#{self.name}: {self.items}'
    
NULL_GROUP = Group()

@dataclass
class Owner():
    output_lines: list[str]
    developer_mode: bool
    identifier: str
    primary_object: Object
    display_mode: str
    def __init__(self, identifier: str, primary_object=NULL_OBJECT):
        self.output_lines = []
        self.developer_mode = False
        self.identifier = identifier
        self.primary_object = primary_object
        self.display_mode = ''
        # If you add anything here, you will need to increase the version.


    def get_object_or_set(self, default: Object):
        if not self.primary_object or self.primary_object == NULL_OBJECT:
            self.primary_object = default
        return self.primary_object
    
    def clear_output(self):
        self.output_lines.clear()

    def read_and_clear_output(self) -> str:
        output = format_counted(count_and_deduplicate(self.output_lines))
        output = '\n'.join(output)
        self.clear_output()
        return output

NULL_OWNER = Owner('')

myself_aliases_list = ['IT', 'ITSELF', 'ME', 'MYSELF', 'SELF', 'HE', 'HIM', 'HIMSELF', 'SHE', 'HER', 'HERSELF', 'THEY', 'THEM', 'THEMSELF', 'SOMEONE', 'SOMEBODY']
myself_aliases = set(myself_aliases_list)
myself_aliases_alternates = r'|'.join(myself_aliases_list)
myself_aliases_regex = re.compile('('+myself_aliases_alternates+')')
object_reference_keywords_list = myself_aliases_list + ['OTHER', 'THIS', 'THAT', 'THESE', 'THOSE', 'NULL', 'SOMETHING']
object_reference_regex = re.compile('('+'|'.join(object_reference_keywords_list)+')')
keywords_list = object_reference_keywords_list + ['AND', 'CREATE', 'GIVE', 'TO', 'REMOVE', 'FROM', 'MOVE', 'GO', 'BRING', 'TOWARDS', 'DO', 'AT', 'TELL', 'DESTROY', 'IF', 'HAS', 'NOT', 'HAVE', 'IS', 'A', 'ARE', 'IN', 'TRUE', 'FALSE', 'PICK', 'STOP', 'FIND', 'SOMETHING', 'NEAREST', 'FARTHEST', 'ALL', 'THAT', 'ONE', 'NOOP']
keywords_set = set(keywords_list)
warning_keywords_set = keywords_set.copy().remove('A')
def alternates_regex_maker(alternate_template, replace_list) -> str:
    return '|'.join(alternate_template.replace('<replace>', element) for element in replace_list)

class CompilationError(RuntimeError):
    def __init__(self, line, type, detail=None, substring='') -> None:
        super().__init__('Compilation Failed', line, type, detail, substring)
        self.line = line; self.type = type; self.detail = detail; self.substring = substring

    def __str__(self) -> str:
        if not self.substring:
            return f'Compilation Failed: {self.type}\nThis line caused a problem:\n`{self.line or 'N/A'}`\n{self.detail}'
        else:
            return f'Compilation Failed: {self.type}\nThis line caused a problem:\n`{self.line or 'N/A'}`\nSpecifically, this part:\n`{self.substring}`\n{self.detail}'
        
    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, CompilationError) and 
            self.__class__ == __value.__class__ and 
            self.line == __value.line and 
            self.type == __value.type and
            self.detail == __value.detail and
            self.substring == __value.substring
        )

    def __hash__(self) -> int:
        return hash((self.line, self.type, self.detail, self.substring, self.__class__.__name__))
        
class CompilationWarning(CompilationError):
    def __str__(self) -> str:
        if not self.substring:
            return f'Compilation Warning: {self.type}\nThis line could cause a problem:\n`{self.line or 'N/A'}`\n{self.detail}'
        else:
            return f'Compilation Warning: {self.type}\nThis line could cause a problem:\n`{self.line or 'N/A'}`\nSpecifically, this part:\n`{self.substring}`\n{self.detail}'

def compile_object_reference(string: str, line=None) -> ObjectReference:
    string = string.strip()
    match string:
        case _ if string in myself_aliases:
            return ObjectReferenceMyself()
        case 'THIS':
            return ObjectReferenceThis()
        case 'THAT':
            return ObjectReferenceThat()
        case 'OTHER':
            return ObjectReferenceOther()
        case 'NULL':
            return ObjectReferenceNull()
        case 'THESE':
            return ObjectReferenceThese()
        case 'THOSE':
            return ObjectReferenceThose()
        case 'SOMETHING':
            return ObjectReferenceSomething()
        case _ if len(string) > 0:
            return ObjectReferenceName(string)
        case _:
            raise CompilationError(line, 'Object Reference', f'Failed to resolve Object Reference; it must be exactly one of the following: {object_reference_keywords_list} or a name of an object definition with 1 or more characters', substring=string)

def compile_line(line: str) -> Opcode:
    line = line.strip()
    if match := re.findall(r'^(.+) AND (.+)$', line):
        return OpAnd(
            operation_1 = compile_line(match[0][0]), 
            operation_2 = compile_line(match[0][1])
        )
    if match := re.findall(r'^CREATE (.+)$', line):
        return OpCreate(
            definition = match[0]
        )
    #if match := re.findall(r'^FIND (.+)$', line):
    #    return OpFind(name = match[0])
    if match := re.findall(r'^GIVE (.+) TO (.+)$', line):
        return OpGive(
            obj_ref = compile_object_reference(match[0][1], line=line),
            item = match[0][0]
        )
    if match := re.findall(r'^REMOVE (.+) FROM (.+)$', line):
        return OpRemove(
            obj_ref = compile_object_reference(match[0][1], line=line),
            item = match[0][0]
        )
    if match := re.findall(r'^MOVE (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF)$', line):
        return OpMove(
            movement = Vector(float(match[0][0]), float(match[0][1]), float(match[0][2]))
        )
    if match := re.findall(r'^GO TO (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF)$', line):
        return OpGoTo(
            destination = Vector(float(match[0][0]), float(match[0][1]), float(match[0][2]))
        )
    if match := re.findall(r'^BRING (.+) TOWARDS (.+)$', line):
        return OpBringTowards(
            moving_obj_ref = compile_object_reference(match[0][0], line=line),
            target_obj_ref = compile_object_reference(match[0][1], line=line)
        )
    if match := re.findall(r'^BRING (.+) TO (.+)$', line):
        return OpBringTo(
            moving_obj_ref = compile_object_reference(match[0][0], line=line),
            target_obj_ref = compile_object_reference(match[0][1], line=line)
        )
    if match := re.findall(r'^DO (.+) (TO|FROM|TOWARDS|AT|THE) (.+)$', line):
        return OpDo(
            verb_name = match[0][0],
            verb_other = compile_object_reference(match[0][2], line=line)
        )
    if match := re.findall(r'^DO (.+)$', line):
        return OpDo(
            verb_name = match[0],
            verb_other = ObjectReferenceMyself()
        )
    if match := re.findall(r'^(TELL|CONTROL) (.+) TO (.+) (TO|FROM|TOWARDS|AT|THE) (.+)$', line):
        return OpTell(
            silent = match[0][0] == 'CONTROL',
            told_object = compile_object_reference(match[0][1], line=line),
            verb_name = match[0][2],
            verb_other = compile_object_reference(match[0][4], line=line)
        )
    if match := re.findall(r'^(TELL|CONTROL) (.+) TO (.+)$', line):
        return OpTell(
            silent = match[0][0] == 'CONTROL',
            told_object = compile_object_reference(match[0][1], line=line),
            verb_name = match[0][2],
            verb_other = compile_object_reference(match[0][1], line=line)
        )
    if match := re.findall(r'^DESTROY (.+)$', line):
        return OpDestroy(
            obj_ref = compile_object_reference(match[0], line=line)
        )
    if match := re.findall(r'^IF (.+?) (HAS NOT|NOT HAVE|NOT HAS|HAVE NOT|HAS|HAVE|IS A|IS NOT A|ARE A|ARE NOT A|IS NOT|ARE NOT|IS IN|IS NOT IN|ARE IN|ARE NOT IN|IS|ARE) (.+)$', line):
        operation = OpIf(Predicate(), False)
        obj_ref = compile_object_reference(match[0][0], line=line)
        if_type = match[0][1]
        failed = False
        if 'NOT' in if_type:
            operation.negated = True
        match if_type:
            case 'HAS'|'HAS NOT'|'NOT HAS'|'HAVE'|'HAVE NOT'|'NOT HAVE':
                operation.predicate = PredicateObjectHas(obj_ref, item=match[0][2])
            case 'IS A'|'IS NOT A'|'ARE A'|'ARE NOT A':
                operation.predicate = PredicateObjectIsA(obj_ref, name=match[0][2])
            case 'IS'|'IS NOT'|'ARE'|'ARE NOT':
                operation.predicate = PredicateObjectIs(obj_ref, match_obj_ref=compile_object_reference(match[0][2], line=line))
            case 'IS IN'|'IS NOT IN'|'ARE IN'|'ARE NOT IN':
                operation.predicate = PredicateObjectIsIn(obj_ref, match_obj_ref=compile_object_reference(match[0][2], line=line))
            case _:
                failed = True
        if not failed:
            return operation
    if match := re.findall(r'^IF (.+?) (EXIST|EXISTS|NOT EXIST|NOT EXISTS)$', line):
        obj_ref = compile_object_reference(match[0][0], line=line)
        negated = 'NOT' in str(match[0][1])
        return OpIf(
            predicate=PredicateObject(obj_ref, negated=negated),
        )
    if match := re.findall(r'^IF (TRUE|NOT TRUE|FALSE|NOT FALSE|MAYBE|NOT MAYBE)$', line):
        if_type: str = match[0]
        negated = 'NOT' in if_type
        if_type = if_type.replace('NOT', '').strip()
        match if_type:
            case 'TRUE':
                return OpIf(PredicateTrue(), negated)
            case 'FALSE':
                return OpIf(PredicateFalse(), negated)
            case 'MAYBE':
                return OpIf(PredicateMaybe(), negated)
    if match := re.findall(r'^SKIP$', line):
        return OpIf(PredicateFalse())
    if match := re.findall(r'^(PICK FROM|PICK) (.+)$', line):
        return OpPick(
            obj_ref = compile_object_reference(match[0][1], line=line)
        )
    if match := re.findall(r'^STOP$', line):
        return OpStop()
    #if match := re.findall(r'^RANGE (\d+|infinity|Infinity|inf|Inf)$', line): TODO: rename
    #    return OpNoop
    if match := re.findall(r'^FIND (SOMETHING|NEAREST|FARTHEST|ALL|.+?) ?(' + alternates_regex_maker('FROM <replace>', object_reference_keywords_list) + r'|) ?(THAT HAS|THAT HAVE|THAT NOT HAS|THAT HAS NOT|THAT NOT HAVE|THAT HAVE NOT|THAT IS A|THAT ARE A|THAT IS NOT A|THAT ARE NOT A|THAT IS ONE OF|THAT ARE ONE OF|THAT IS NOT ONE OF|THAT ARE NOT ONE OF|THAT IS NOT|THAT ARE NOT|THAT IS|THAT ARE|) ?(.*)$', line):
        selector_type: str = match[0][0]
        selector: Selector = NULL_SELECTOR
        find_multiple = False
        find_from = str(match[0][1]).replace('FROM ', '')
        obj_ref_from = ObjectReferenceAll() if not find_from else compile_object_reference(find_from)
        predicate_type = str(match[0][2])
        predicate_negated = False
        if 'NOT' in predicate_type:
            predicate_negated = True
        predicate: Predicate = NULL_PREDICATE
        predicate_value = str(match[0][3])
        match selector_type:
            case 'SOMETHING':
                selector = SelectorRandom()
            case 'NEAREST':
                selector = SelectorNearest()
            case 'FARTHEST':
                selector = SelectorFarthest()
            case 'ALL':
                selector = SelectorAll()
                find_multiple = True
            case _:
                name = selector_type
                return OpFind(
                    obj_ref_from=obj_ref_from,
                    selector=SelectorNearest(),
                    find_multiple=False,
                    predicate=PredicateObjectIsA(obj_ref=NULL_OBJECT_REFERENCE, name=name, negated=predicate_negated)
                )
        match predicate_type:
            case '' if not predicate_value:
                predicate = PredicateTrue()
            case 'THAT HAS' | 'THAT HAVE' | 'THAT HAS NOT' | 'THAT NOT HAS' | 'THAT HAVE NOT' | 'THAT NOT HAVE' if predicate_value:
                predicate = PredicateObjectHas(obj_ref=NULL_OBJECT_REFERENCE, item=predicate_value, negated=predicate_negated)
            case 'THAT IS A' | 'THAT ARE A' | 'THAT IS NOT A' | 'THAT ARE NOT A' if predicate_value:
                predicate = PredicateObjectIsA(obj_ref=NULL_OBJECT_REFERENCE, name=predicate_value, negated=predicate_negated)
            case 'THAT IS' | 'THAT ARE' | 'THAT IS NOT' | 'THAT ARE NOT' if predicate_value:
                predicate = PredicateObjectIs(obj_ref=NULL_OBJECT_REFERENCE, match_obj_ref=compile_object_reference(predicate_value, line=line), negated=predicate_negated)
            case 'THAT IS ONE OF' | 'THAT ARE ONE OF' | 'THAT IS NOT ONE OF' | 'THAT ARE NOT ONE OF' if predicate_value:
                predicate = PredicateObjectIsIn(obj_ref=NULL_OBJECT_REFERENCE, match_obj_ref=compile_object_reference(predicate_value, line=line), negated=predicate_negated)
            case _:
                if not predicate_value:
                    raise CompilationError(line, 'Code', 'FIND command is missing a value')
                raise CompilationError(line, 'Code', 'FIND command has malformed, unsupported, or misspelled predicate')
        return OpFind(
            obj_ref_from=obj_ref_from,
            selector=selector,
            find_multiple=find_multiple,
            predicate=predicate
        )
    if match := re.findall(r'^OUTPUT TO (.+?) (.+)$', line):
        recipient = compile_object_reference(match[0][0])
        parts: list = re.split(object_reference_regex, match[0][1])
        for i, part in enumerate(parts):
            if part in object_reference_keywords_list:
                parts[i] = compile_object_reference(part, line=line)
        return OpOutputTo(
            stuff=parts,
            recipient=recipient
        )
    if match := re.findall(r'^RAWOUTPUT TO (.+?) (.+)$', line):
        recipient = compile_object_reference(match[0][0])
        string = match[0][1]
        return OpRawOutputTo(
            string=string,
            recipient=recipient
        )
    if match := re.findall(r'^OUTPUT (.+)$', line):
        parts: list = re.split(object_reference_regex, match[0])
        for i, part in enumerate(parts):
            if part in object_reference_keywords_list:
                parts[i] = compile_object_reference(part, line=line)
        return OpOutput(
            stuff=parts
        )
    if match := re.findall(r'^RAWOUTPUT (.+)$', line):
        string = match[0]
        return OpRawOutput(
            string=string
        )
    if match := re.findall(r'^MUTE$', line):
        return OpMute()
    if match := re.findall(r'^UNMUTE$', line):
        return OpUnmute()
    if match := re.findall(r'^UNSTOP$', line):
        return OpUnstop()
    if match := re.findall(r'^(NOOP|\|.*)$', line):
        return OpNoop
    
    raise CompilationError(line, 'Code', 'This is not a valid command. It was not recognized by any command format.')
    return OpNoop

def parse_list(string: str) -> list[str]:
    if not string or string == 'NOTHING':
        return []
    return string.strip().replace(', ',',').replace(', ',',').split(',')

def parse_tenses(string: str, line=None) -> dict[str, str]:
    word_list = string.strip().replace(', ',',').replace(', ',',').split(',')
    try:
        assert len(word_list) == 5
        return {'simple': word_list[0], 'plural': word_list[1], 'present': word_list[2], 'past': word_list[3], 'future': word_list[4]}
    except (IndexError, AssertionError):
        raise CompilationError(line, 'Tenses', 'Tense format invalid: must be <simple>, <plural>, <present continuous>, <past>, <future>. Ex: dance, dances, dancing, danced, will dance', substring=string) from None
    
def parse_float(number: str, line=None) -> float:
    try:
        return float(number)
    except ValueError:
        raise CompilationError(line, 'Number', 'This cannot be read as a number.', substring=number) from None

def compile(text: str, ctx: Ctx, add_to_ctx=False, permit_place=False):
    mode = None
    object_construct: ObjectDefinition = NULL_OBJECT_DEFINITION
    verb_construct: Verb = NULL_VERB
    group_construct: Group = NULL_GROUP
    construction_in_progress = False
    procedure_construct: Procedure = NULL_PROCEDURE
    source_construct = ''
    completed_objects: list[ObjectDefinition] = []
    completed_verbs: list[Verb] = []
    completed_groups: list[Group] = []
    warnings = []
    def complete_object():
        nonlocal ctx, object_construct, construction_in_progress, mode, source_construct
        if not object_construct.name:
            raise CompilationError(None, 'Object', 'Object definition is missing a name. Define one using `NAME:`')
        object_construct.source = source_construct
        completed_objects.append(object_construct)
        if add_to_ctx:
            ctx.object_definitions[object_construct.name] = object_construct
        print(f'Constructed Object {object_construct.name}')
        object_construct = NULL_OBJECT_DEFINITION
        source_construct = ''
        construction_in_progress = False
        mode = None
    def complete_verb():
        nonlocal ctx, verb_construct, construction_in_progress, mode, source_construct
        if not verb_construct.name:
            raise CompilationError(None, 'Verb', 'Verb definition is missing a name. Define one using `NAME:`')
        if not verb_construct.tenses:
            raise CompilationError(None, 'Verb', 'Verb definition is missing tenses. Define one using `TENSES:`\nTense format must be <simple>, <plural>, <present continuous>, <past>, <future>. Ex: dance, dances, dancing, danced, will dance')
        verb_construct.source = source_construct
        completed_verbs.append(verb_construct)
        if add_to_ctx:
            ctx.verbs[verb_construct.name] = verb_construct
        print(f'Constructed Verb {verb_construct.name}')
        verb_construct = NULL_VERB
        source_construct = ''
        construction_in_progress = False
        mode = None
    def complete_group():
        nonlocal ctx, group_construct, construction_in_progress, mode, source_construct
        if not group_construct.name:
            raise CompilationError(None, 'Group', 'Group definition is missing a name. Define one using `NAME:`')
        group_construct.source = source_construct
        completed_groups.append(group_construct)
        if add_to_ctx:
            ctx.groups[group_construct.name] = group_construct
        print(f'Constructed Group {group_construct.name}')
        group_construct = NULL_GROUP
        source_construct = ''
        construction_in_progress = False
        mode = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        operation = None
        if mode == None:
            if line == 'OBJECT':
                mode = 'OBJECT'
                construction_in_progress = True
                object_construct = ObjectDefinition()
                source_construct += raw_line + '\n'
                continue
            if line == 'VERB':
                mode = 'VERB'
                construction_in_progress = True
                verb_construct = Verb()
                source_construct += raw_line + '\n'
                continue
            if line == 'GROUP':
                mode = 'GROUP'
                construction_in_progress = True
                group_construct = Group()
                source_construct += raw_line + '\n'
                continue
            if permit_place and (match := re.findall(r'^PLACE (.+) AT (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF|nan|NAN) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF|nan|NAN) (-?\d+|-?infinity|-?Infinity|-?INFINITY|-?inf|-?Inf|-?INF|nan|NAN)$', line)):
                ctx.spawn(match[0][0], Vector(parse_float(match[0][1]), parse_float(match[0][2]), parse_float(match[0][3])))
                print(f'Placed {match[0][0]}')
                continue
            if not (match := re.findall(r'^\s*$', line)):
                raise CompilationError(line, 'Text', 'Unknown thingy. Was looking for OBJECT or VERB or GROUP to start defining something. Did you close the previous object\'s definition too early by including an empty line?')
        if mode == 'CODE OBJECT' or mode == 'CODE VERB':
            if re.findall(r'[^\\]:', line) and not raw_line.startswith('  '):
                # this line needs to be parsed as a declaration instead
                mode = mode.replace('CODE ', '') # 'OBJECT' or 'VERB'
            elif (match := re.findall(r'^\s*$', line)):
                if mode == 'CODE OBJECT':
                    complete_object()
                if mode == 'CODE VERB':
                    complete_verb()
            else:
                operation = compile_line(line)
                operation.check_for_warnings(ctx, line, warnings)
                procedure_construct.opcodes.append(operation)
                #print(operation)
        if mode == 'OBJECT':
            if (match := re.findall(r'^(.+?): (.+)$', line)):
                attribute = match[0][0]
                value = match[0][1]
                match attribute:
                    case 'NAME':
                        object_construct.name = value
                    case 'INVENTORY':
                        object_construct.default_inventory = parse_list(value)
                    case 'ACTIONS':
                        object_construct.actions = parse_list(value)
                    case 'AI':
                        object_construct.AI = parse_AI(value, line)
                    case 'OWNER':
                        object_construct.owner = value
                    case 'INTERACTION RADIUS':
                        object_construct.interaction_radius = parse_float(value, line)
                    case _:
                        raise CompilationError(line, 'Object', 'Attempted to assign an invalid, unsupported, or misspelled property on left side of `:`', substring=attribute)
            elif (match := re.findall(r'^(WHEN|BEFORE) MOVED (INTO|IN TO|OUTOF|OUT OF):$', line)):
                procedure_construct = Procedure()
                hook = str(match[0][0])
                direction = str(match[0][1])
                if hook == 'BEFORE' and direction[0] == 'I':
                    object_construct.before_moved_into_procedure = procedure_construct
                elif hook == 'BEFORE' and direction[0] == 'O':
                    object_construct.before_moved_out_of_procedure = procedure_construct
                elif hook == 'WHEN' and direction[0] == 'I':
                    object_construct.when_moved_into_procedure = procedure_construct
                elif hook == 'WHEN' and direction[0] == 'O':
                    object_construct.when_moved_out_of_procedure = procedure_construct
                mode = "CODE OBJECT"
            elif (match := re.findall(r'^(WHEN|BEFORE) (.+?) (.+) (.+?):$', line)) or (match := re.findall(r'^(WHEN|BEFORE) (.+?) (.+):$', line)):
                hook = match[0][0]
                acting_object = match[0][1]
                verb = match[0][2]
                receiving_object = match[0][3] if len(match[0]) == 4 else 'OTHER'
                procedure_construct = Procedure()
                if hook == 'BEFORE' and acting_object in myself_aliases and receiving_object == 'OTHER':
                    object_construct.before_perform_action_procedures[verb] = procedure_construct
                elif hook == 'BEFORE' and acting_object == 'OTHER' and receiving_object in myself_aliases:
                    object_construct.before_receive_action_procedures[verb] = procedure_construct
                elif hook == 'WHEN' and acting_object in myself_aliases and receiving_object == 'OTHER':
                    object_construct.when_perform_action_procedures[verb] = procedure_construct
                elif hook == 'WHEN' and acting_object == 'OTHER' and receiving_object in myself_aliases:
                    object_construct.when_receive_action_procedures[verb] = procedure_construct
                else:
                    raise CompilationError(line, 'Object', f'{hook} procedure declaration incorrect. Must be of the form {hook} (IT|OTHER) <verb> (OTHER|IT), or {hook} IT <verb>. \'IT\' can be replaced with any other reference meaning "itself": {myself_aliases_list}')
                mode = "CODE OBJECT"
            elif (match := re.findall(r'^INITIALIZE:$', line)):
                procedure_construct = Procedure()
                object_construct.initialize_procedure = procedure_construct
                mode = "CODE OBJECT"
            elif (match := re.findall(r'^\s*$', line)):
                complete_object()
            else:
                raise CompilationError(line, 'Object', 'This line couldn\'t be interpreted, something weird is in it')
        elif mode == 'VERB':
            if (match := re.findall(r'^(.+?): (.+)$', line)):
                attribute = match[0][0]
                value = match[0][1]
                match attribute:
                    case 'NAME':
                        verb_construct.name = value
                    case 'TENSES':
                        verb_construct.tenses = parse_tenses(value, line=line)
                    case _:
                        raise CompilationError(line, 'Verb', 'Attempted to assign an invalid, unsupported, or misspelled property on left side of `:`', substring=attribute)
            elif (match := re.findall(r'^WHEN (.+?) ' + verb_construct.name + r'( OTHER:|:)$', line)):
                procedure_construct = Procedure()
                verb_construct.procedure = procedure_construct
                mode = "CODE VERB"
            elif (match := re.findall(r'^\s*$', line)):
                complete_verb()
            else:
                raise CompilationError(line, 'Verb', 'This line couldn\'t be interpreted, something weird is in it')
        elif mode == 'GROUP':
            if (match := re.findall(r'^(.+?): (.+)$', line)):
                attribute = match[0][0]
                value = match[0][1]
                match attribute:
                    case 'NAME':
                        group_construct.name = value
                    case 'ITEMS':
                        group_construct.items = parse_list(value)
                    case _:
                        raise CompilationError(line, 'Group', 'Attempted to assign an invalid, unsupported, or misspelled property on left side of `:`', substring=attribute)
            elif (match := re.findall(r'^\s*$', line)):
                complete_group()
            else:
                raise CompilationError(line, 'Group', 'This line couldn\'t be interpreted, something weird is in it')
        
        if mode is not None:
            source_construct += raw_line + '\n'
        if operation:
            print(f'Compiled "{line}" -> {operation}')
        else:
            print(f'Compiled "{line}"')

    # instantiate in-progress constructs at end
    if mode == 'OBJECT' or mode == 'CODE OBJECT':
        complete_object()
    if mode == 'VERB' or mode == 'CODE VERB':
        complete_verb()
    if mode == 'GROUP':
        complete_group()
    # if add_to_ctx:
    #     for obj_def in completed_objects:
    #         ctx.object_definitions[obj_def.name] = obj_def
    #     for verb in completed_verbs:
    #         ctx.verbs[verb.name] = verb
    return (completed_objects, completed_verbs, completed_groups, warnings)

def eat_generator(generator):
    try:
        next(generator)
    except StopIteration:
        pass

import os

TestFile = ''
with open(os.path.normpath(os.path.join(__file__, '..', "WackyCodexTest.txt"))) as load_file:
    TestFile = load_file.read()

DefaultFile = ''
with open(os.path.normpath(os.path.join(__file__, '..', "WackyCodexDefault.txt"))) as load_file:
    DefaultFile = load_file.read()

ExampleFile = ''
with open(os.path.normpath(os.path.join(__file__, '..', "WackyCodexExample.txt"))) as load_file:
    ExampleFile = load_file.read()

if __name__ == "__main__":
    ctx = Ctx()
    with open("WackyCodexTest.txt") as load_file:
        load_string = load_file.read()
        eat_generator(ctx.compile_and_prompt(load_string, auto_confirm=True))
        gold = ctx.spawn('Gold', Vector.zero())
        gold.do('test', gold, ctx=ctx)
        create_player = ctx.create_player('Airtoum', '123123')
        diffs, warnings = next(create_player)
        print("\n".join(diffs))
        send_and_finish(create_player, True)
        define_gold = ctx.compile_and_prompt('OBJECT\nNAME: Gold\nINVENTORY: Golden, Small')
        diffs, warnings = next(define_gold)
        print("\n".join(diffs))
        send_and_finish(define_gold, True)
        define_gold_2 = ctx.compile_and_prompt('OBJECT\nNAME: Gold\nINVENTORY: Golden, Small')
        diffs, warnings = next(define_gold_2)
        print("\n".join(diffs))
        send_and_finish(define_gold, True)
        ctx.error('This', gold, 'is a gold')
        print("\n".join(ctx.output_lines))
        print(ctx.lookup('test'))
        assert count_and_deduplicate(['a','a','b','b','b','a','c','d','e']) == [('a',2),('b',3),('a',1),('c',1),('d',1),('e',1)]
        assert count_and_deduplicate(['a','a']) == [('a',2)]
        assert count_and_deduplicate(['a']) == [('a',1)]
        assert count_and_deduplicate([]) == []
        assert (value := Vector(0,1,0).describe_relative()) == '1 north'
        assert (value := Vector(0,-1,0).describe_relative()) == '1 south'
        assert (value := Vector(-1,0,0).describe_relative()) == '1 west'
        assert (value := Vector(1,0,0).describe_relative()) == '1 east'
        assert (value := Vector(0,0,1).describe_relative()) == '1 up'
        assert (value := Vector(0,0,-1).describe_relative()) == '1 down'
        assert (value := Vector(2,0,-1).describe_relative()) == '2 east, 1 down'
        assert (value := Vector(-4,5,-1).describe_relative()) == '4 west, 5 north, 1 down'
        assert (value := Vector(-1,-1,0).describe_relative()) == '1 west, 1 south'
        assert CompilationError('abc','def','ghi','jkl') == CompilationError('abc','def','ghi','jkl')
        assert CompilationError('abc','def','ghi','jkl') != CompilationError('mno','pqr','stu','vwx')
        assert CompilationWarning('abc','def','ghi','jkl') == CompilationWarning('abc','def','ghi','jkl')
        assert CompilationWarning('abc','def','ghi','jkl') != CompilationWarning('mno','pqr','stu','vwx')
        assert CompilationError('abc','def','ghi','jkl') != CompilationWarning('abc','def','ghi','jkl')
        assert CompilationWarning('abc','def','ghi','jkl') != CompilationError('abc','def','ghi','jkl')
        ctx.clear_output()
        north = ctx.spawn('North', Vector.zero(), output_creation=True)
        north = ctx.spawn('North', Vector.zero(), output_creation=True)
        print(ctx.read_and_clear_output())
        assert subfinitize(0) == 0
        assert subfinitize(3) == 0
        assert subfinitize(-3) == 0
        assert subfinitize(inf) == 1
        assert subfinitize(-inf) == -1
        assert isnan(subfinitize(nan))
        assert Vector(40, 50, 0).finitize() == Vector(40, 50, 0)
        assert Vector(0, inf, 0).finitize() == Vector(0, 1, 0)
        assert Vector(-inf, -inf, 18).finitize() == Vector(-1, -1, 0)
        v1 = Vector(0, 0, 0)
        v2 = Vector(0, inf, 0)
        va = (v2 - v1)
        va = va.normalized()
        assert va == Vector(0, 1, 0)
        va = va + v1
        eat_generator(ctx.compile_and_prompt('PLACE Wall AT 2 3 4', auto_confirm=True, permit_place=True))
        assert ctx.objects[3]
        assert ctx.objects[3].definition == 'Wall'
        assert ctx.objects[3].position == Vector(2, 3, 4)
        test_group = Group()
        test_group.items.append('eggs')
        assert 'eggs' in test_group
    ctx = Ctx()
    with open("WackyCodexExample.txt") as load_file:
        load_string = load_file.read()
        compile(load_string, ctx, add_to_ctx=True, permit_place=True)
        
        print('Goodbye')
