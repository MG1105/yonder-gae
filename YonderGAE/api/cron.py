from db import YonderDb
import cloudstorage as gcs
import logging

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

class Cron (object):

    def run(self):
        yonderdb = YonderDb()
        ids = yonderdb.cleanup()
        yonderdb.cron_set_invisible()
        # yonderdb.fake_rating()
        for id in ids:
            file_name = "/yander/" + id + ".mp4"
            logging.info("Deleting %s" % id)
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            try:
                gcs.delete(file_name, retry_params=write_retry_params) # when removing invisible admin videos, 14 first videos wont be there
            except gcs.NotFoundError:
                logging.warn("Video not found %s" % id)
                pass
        yonderdb.set_hot_score()