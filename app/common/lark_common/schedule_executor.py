# -*- coding: utf-8 -*-
"""
Ceph Performance Message Broker Provider
"""

from apscheduler.schedulers.background import BackgroundScheduler


class CronDefinition(object):
    def __init__(self):
        self.scheduler_second = None
        self.scheduler_minute = None
        self.scheduler_hour = None
        self.scheduler_day = None
        self.scheduler_week = None
        self.scheduler_day_of_week = None
        self.scheduler_month = None
        self.scheduler_year = None


# Performance Executor
class ScheduleHelper(object):
    __scheduler = BackgroundScheduler()

    # Init Scheduler
    def __init__(self):
        pass

    def add_job(self, job_id, name, func, args=None, kwargs=None, cron_definition=None, misfire_grace_time=None):
        if cron_definition is None:
            return

        self.__scheduler.add_job(func, 'cron', args=args, kwargs=kwargs,
                                 second=cron_definition.scheduler_second,
                                 minute=cron_definition.scheduler_minute,
                                 hour=cron_definition.scheduler_hour,
                                 day=cron_definition.scheduler_day,
                                 week=cron_definition.scheduler_week,
                                 day_of_week=cron_definition.scheduler_day_of_week,
                                 month=cron_definition.scheduler_month,
                                 year=cron_definition.scheduler_year,
                                 misfire_grace_time=misfire_grace_time,
                                 name=name,
                                 id=job_id)

    # Start scheduler
    def start(self):
        try:
            self.__scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.__scheduler.shutdown()

    # Stop scheduler
    def pause_job(self, job_id):
        self.__scheduler.pause_job(job_id)

    # Reset scheduler
    def resume_job(self, job_id):
        self.__scheduler.resume_job(job_id)

    def shutdown(self):
        self.__scheduler.shutdown()

    def print_jobs(self):
        self.__scheduler.print_jobs()
