import logging
import cloudstorage as gcs
import webapp2

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
										  max_delay=5.0,
										  backoff_factor=2,
										  max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)

class MainPage(webapp2.RequestHandler):
	"""Main page for GCS demo application."""

	def post(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Hello Medi Gouta!')
		bucket_name = "yander"
		bucket = '/' + bucket_name
		try:
			self.create_file("/yander/myvideo.mp4")
		except Exception, e:
			logging.exception(e)
			#self.delete_files()
			self.response.write('\n\nThere was an error running the demo! Please check the logs for more details.\n')
		else:
			self.response.write('\n\nThe demo ran successfully!\n')

	def create_file(self, filename):
		"""Create a file.
		The retry_params specified in the open call will override the default
		retry params for this particular file handle.
		Args:
		  filename: filename.
		"""
		self.response.write('Creating file %s\n' % filename)

		write_retry_params = gcs.RetryParams(backoff_factor=1.1)
		gcs_file = gcs.open(filename,
							'w',
							content_type='video/mp4',
							options={'x-goog-meta-foo': 'foo',
									 'x-goog-meta-bar': 'bar'},
							retry_params=write_retry_params)
		file_content = self.request.POST.multi["'uploadedfile'"].file.read()
		gcs_file.write(file_content)
		gcs_file.close()

app = webapp2.WSGIApplication([('/upload', MainPage),], debug=True)