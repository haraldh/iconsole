# iconsole
Reverse engineering of the iconsole+ bike computer serial protocol.

Broadcasts the power and speed on the ANT network.

## Requirements

```
$ pip install --user requirements.txt
```

## Usage

```
$ python iConsole.py <ANT Network Key in ASCII Hex>
```

Use the ANT+ network key to record the data with ANT+ compatible devices, such as a bike computer or fitness watch.