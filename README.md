# remote-tasks

This project has a simple goal: To run remote tasks  
In order to achieve this, we need to install `fabric2`:

```
$ pip install -r requirements.pip
```

Then we need to create our `fabric.yaml` where we'll configure the servers and other settings that will be executed.

```
$ fab create-yaml
```

once `fabric.yaml` is written, we can run:

```
$ fab main
```


And that's it!

## License

WTFPL
