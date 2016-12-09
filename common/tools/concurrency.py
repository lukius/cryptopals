import multiprocessing
import threading
import Queue


class ConcurrentTaskManager(object):
    
    DEFAULT_WORKERS = 4
    
    def __init__(self, workers=None):
        self.task_queue = Queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        self.workers = workers or self.DEFAULT_WORKERS
        self.pool = WorkerPool(self.workers)
        
    def pool_size(self):
        return self.workers
        
    def add_task(self, task):
        self.task_queue.put(task)
        
    def compete(self, tasks):
        finished_cond = threading.Condition()
        
        def _on_finished(task):
            self.task_finished = task
            with finished_cond:
                finished_cond.notify_all()
                
        def _task_on_finished(task):
            task_on_finished = getattr(task, 'on_finished')
            def _f():
                task_on_finished()
                _on_finished(task)
            return _f
        
        self.task_finished = None

        for task in tasks:
            setattr(task, 'on_finished', _task_on_finished(task))
            self.add_task(task)
            
        with finished_cond:
            finished_cond.wait()
            task_finished = self.task_finished
            
        self.stop()
        
        return task_finished
    
    def _run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            self.pool.assign(task)
        with self.task_queue.all_tasks_done:
            self.task_queue.all_tasks_done.notify_all()

    def join(self):
        if self.thread.is_alive():
            self.task_queue.put(None)
            with self.task_queue.all_tasks_done:
                self.task_queue.all_tasks_done.wait()
        self.pool.join()
    
    def stop(self):
        self.task_queue.put(None)
        self.pool.stop()
    
    def __enter__(self, *args, **kwargs):
        return self
    
    def __exit__(self, *args, **kwargs):
        self.join()
        
        
class WorkerPool(object):
    
    def __init__(self, size):
        self.size = size
        self.workers = [Worker(self) for _ in xrange(size)]
        self.worker_finished_ev = multiprocessing.Event()
        self.lock = multiprocessing.Lock()
        self.worker_finished = None
        self.tasks_finished = list()
        
    def assign(self, task):
        worker = self._wait_for_free_worker()
        worker.run(task)
    
    def join(self):
        for worker in self.workers:
            worker.join()
            
    def stop(self):
        for worker in self.workers:
            worker.stop()
            
    def _on_worker_finished(self, worker, task):
        with self.lock:
            self.tasks_finished.append(task)
            self.worker_finished = worker
            self.worker_finished_ev.set()
    
    def _wait_for_free_worker(self):
        while True:
            for worker in self.workers:
                if worker.is_idle():
                    return worker

            self.worker_finished_ev.wait()
            with self.lock:
                self.worker_finished_ev.clear()
    
    
class Worker(object):
    
    def __init__(self, pool):
        self.pool = pool
        self.idle = True
        self.process = None
        self.monitor = None
        self.lock = threading.Lock()
        
    def is_idle(self):
        with self.lock:
            return self.idle
    
    def join(self):
        with self.lock:
            idle = self.idle
        if not idle and self.process is not None:
            self.monitor.join()
            
    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.monitor.join()
        
    def _join_process(self, task):
        self.process.join()
        with self.lock:
            self.idle = True
        self.pool._on_worker_finished(self, task)
        task.on_finished()
        self.process = None
        
    def run(self, task):
        with self.lock:
            self.idle = False
            self.process = multiprocessing.Process(target=task.run)
            self.monitor = threading.Thread(target=self._join_process,
                                            args=(task,))
            self.process.daemon = True
            self.monitor.daemon = True
            self.process.start()
            self.monitor.start()
        
        
class ConcurrentTask(object):
    
    def __init__(self):
        self.queue = multiprocessing.Queue()
        
    def on_finished(self):
        pass
    
    def run(self):
        raise NotImplementedError