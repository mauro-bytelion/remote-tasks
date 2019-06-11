try:
    from invoke.vendor.six.moves.queue import Queue
except ImportError:
    from six.moves.queue import Queue

from invoke.util import ExceptionHandlingThread

from fabric.exceptions import GroupException
from fabric.group import thread_worker
from fabric import (
    Connection,
    GroupResult,
    SerialGroup,
    ThreadingGroup,
)


def thread_worker_sudo(cxn, queue, args, kwargs):
    result = cxn.sudo(*args, **kwargs)
    # TODO: namedtuple or attrs object?
    queue.put((cxn, result))


class SerialGroupSudo(SerialGroup):
    def sudo(self, *args, **kwargs):
        results = GroupResult()
        excepted = False
        for cxn in self:
            try:
                results[cxn] = cxn.sudo(*args, **kwargs)
            except Exception as e:
                results[cxn] = e
                excepted = True
        if excepted:
            raise GroupException(results)
        return results


class ThreadingGroupSudo(ThreadingGroup):

    def run(self, *args, **kwargs):
        results = GroupResult()
        queue = Queue()
        threads = []
        for cxn in self:
            my_kwargs = dict(cxn=cxn, queue=queue, args=args, kwargs=kwargs)
            thread = ExceptionHandlingThread(
                target=thread_worker, kwargs=my_kwargs
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            # TODO: configurable join timeout
            # TODO: (in sudo's version) configurability around interactive
            # prompting resulting in an exception instead, as in v1
            thread.join()
        # Get non-exception results from queue
        while not queue.empty():
            # TODO: io-sleep? shouldn't matter if all threads are now joined
            cxn, result = queue.get(block=False)
            # TODO: outstanding musings about how exactly aggregate results
            # ought to ideally operate...heterogenous obj like this, multiple
            # objs, ??
            results[cxn] = result
        # Get exceptions from the threads themselves.
        # TODO: in a non-thread setup, this would differ, e.g.:
        # - a queue if using multiprocessing
        # - some other state-passing mechanism if using e.g. coroutines
        # - ???
        excepted = False
        for thread in threads:
            wrapper = thread.exception()
            if wrapper is not None:
                # Outer kwargs is Thread instantiation kwargs, inner is kwargs
                # passed to thread target/body.
                cxn = wrapper.kwargs["kwargs"]["cxn"]
                results[cxn] = wrapper.value
                excepted = True
        if excepted:
            raise GroupException(results)
        return results

    def sudo(self, *args, **kwargs):
        results = GroupResult()
        queue = Queue()
        threads = []
        for cxn in self:
            my_kwargs = dict(cxn=cxn, queue=queue, args=args, kwargs=kwargs)
            thread = ExceptionHandlingThread(
                target=thread_worker_sudo, kwargs=my_kwargs
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            # TODO: configurable join timeout
            # TODO: (in sudo's version) configurability around interactive
            # prompting resulting in an exception instead, as in v1
            thread.join()
        # Get non-exception results from queue
        while not queue.empty():
            # TODO: io-sleep? shouldn't matter if all threads are now joined
            cxn, result = queue.get(block=False)
            # TODO: outstanding musings about how exactly aggregate results
            # ought to ideally operate...heterogenous obj like this, multiple
            # objs, ??
            results[cxn] = result
        # Get exceptions from the threads themselves.
        # TODO: in a non-thread setup, this would differ, e.g.:
        # - a queue if using multiprocessing
        # - some other state-passing mechanism if using e.g. coroutines
        # - ???
        excepted = False
        for thread in threads:
            wrapper = thread.exception()
            if wrapper is not None:
                # Outer kwargs is Thread instantiation kwargs, inner is kwargs
                # passed to thread target/body.
                cxn = wrapper.kwargs["kwargs"]["cxn"]
                results[cxn] = wrapper.value
                excepted = True
        if excepted:
            raise GroupException(results)
        return results
