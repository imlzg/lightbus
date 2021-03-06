Lightbus processes automatically generate and share schemas for their available APIs.
These schemes can be used to validate the following:

* Remote procedure call parameters
* Remote procedure call return values
* Event parameters

These schemas are shared using the configured `SchemaTransprt` (Redis, by default).
Each Lightbus process will monitor for any schema changes.

## Specifying types

Lightbus will create a schema by inspecting the parameters
and [type hints] of your APIs' events and procedures.

You can use the schema functionality without type hints, but the level of validation
provided will be limited to ensuring parameter names match what is expected.

The [schema protocol reference] covers the specifics of the schema data format.

## Supported data types

Lightbus maps Python types to JSON types. While Python-specific values can be sent using Lightbus,
these values will arrive in their JSON form. For example, if you send a `string` then a `string` will arrive.
However, if you send the `Decimal` value `3.124`, then you will receive the `string` value `3.124` instead.

The following types are reasonably interoperable:


| Python type sent                          | JSON schema interpretation                        | Type received
| ----------------------------------------- | ------------------------------------------------- | ---------------
| `str`                                     | `string`                                          | `str`
| `int`, `float`                            | `number`                                          | `int`, `float`
| `bool   `                                 | `boolean`                                         | `bool`
| `list`, `tuple`                           | `array`                                           | `list`
| `None`                                    | `null`                                            | `None`
| `dict`, `Mapping`, etc                    | `object`                                          | `dict`
| `Mapping[str, ...]`                       | `object`, with [pattern properties] set           | `dict`
| `Tuple[A, B, C]`                          | `array` with [maxItems/minItems] and [items] set. | `list`

The following types will be successfully encoded and sent, but will arrive as their encoded equivalent:

| Python type                               | JSON Schema type                                  | Value arrives as
| ----------------------------------------- | ------------------------------------------------- | ---------------
| `bytes`, `Decimal`, `complex`             | `string`                                          | `str`
| `datetime`, `date`                        | `str`                                             | `str` (ISO 8601)
| `NamedTuple` with annotations             | `object` with [specific typed properties]         | `dict`
| `object` with annotations                 | `object` with [specific typed properties]         | `dict`

Lightbus can also handle the following:

| Python type                               | JSON Schema type
| ----------------------------------------- | -------------------------------------------------
| `Any`                                     | `{}` (any value)
| `Union[...]`                              | `oneOf{...}` (see [oneOf])
| `Enum`                                    | Sets [enum] property

## Automatic validation

By default this validation will be validated in both the
incoming and outgoing directions. Outgoing refers to
the dispatching of events or procedure calls to the bus.
Incoming refers to the processing of procedure calls or
handling of received events.

You can configuring this using the ``validate``
[configuration](configuration.md) option.

### Validation configuration

You can configure the validation behaviour in your
bus' `config.yaml`.

#### `validate (bool) = true`

You can enable/disable validation using a boolean true/false flag:

```yaml
# In config.yaml
apis:
    default:
        validate: false
```

For finer grained control you can specify individual flags for incoming/outgoing
validation:

```yaml
# In config.yaml
apis:
    default:
        validate:
          outgoing: true
          incoming: false
```

#### `strict_validation (bool) = false`

If `strict_validation` is `true` then calling a procedure for which no schema exists will
result in an error:

```yaml
# In config.yaml
apis:
    default:
        strict_validation: true
```

## Manual validation

Lightbus supports manually loading your bus' schema into your bus client. 
For example, you may [take a dump of your production bus schema](command-line-use/dumpschema.md)
and use it to test/develop against either in your local development environment or 
in any automated testing system.

You can load a local schema as follows:

```python
from bus import bus

# Either load form a single file
bus.schema.load_local("/path/to/local/bus-schema.json")

# ... or load all schemas in a directory
bus.schema.load_local("/path/to/local/schema/")
```

Your bus client will now use the specified schema to validate RPCs and events.

Parameters and responses may also be directly validated so you need:

* Event (parameters): `bus.my_api.my_event.validate_parameters(parameters)`
* RPC (parameters): `bus.my_api.my_rpc.validate_parameters(parameters)`
* RPC (response): `bus.my_api.my_rpc.validate_response(response)`

You can use these methods to manually validate parameters or response values against 
the locally loaded schema.

[type hints]: https://docs.python.org/3/library/typing.html
[oneOf]: https://json-schema.org/understanding-json-schema/reference/combining.html#oneof
[enum]: https://json-schema.org/understanding-json-schema/reference/generic.html#enumerated-values
[pattern properties]: https://json-schema.org/understanding-json-schema/reference/object.html#pattern-properties
[specific typed properties]: https://json-schema.org/understanding-json-schema/reference/object.html#properties
[maxItems/minItems]: https://json-schema.org/understanding-json-schema/reference/array.html#length
[items]: https://json-schema.org/understanding-json-schema/reference/array.html#tuple-validation
[schema protocol reference]: protocols/schema.md
