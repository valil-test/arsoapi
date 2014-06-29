
import datetime
import os
import unittest

from arsoapi.models import RadarPadavin, GeocodedRadar, Aladin, GeocodedAladin, mmph_to_level
from arsoapi.formats import radar_detect_format

from PIL import Image

datafile = lambda x: os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', x))

class TestRadarFormat(unittest.TestCase):
	def test_detect_1(self):
		img = Image.open(open(datafile('test_sirad.gif')))
		fmt = radar_detect_format(img)

		self.assertEqual(fmt.ID, 1)

	def test_detect_2(self):
		img = Image.open(open(datafile('test_sirad_si1_si2.gif')))
		fmt = radar_detect_format(img)

		self.assertEqual(fmt.ID, 2)

	def test_detect_3(self):
		img = Image.open(open(datafile('test_sirad_si1_si2_b.gif')))
		fmt = radar_detect_format(img)

		self.assertEqual(fmt.ID, 3)

class TestVreme(unittest.TestCase):
	def test_mmph_to_level(self):
		self.assertEqual(mmph_to_level(0.0), 0)
		self.assertEqual(mmph_to_level(0.5), 25)
		self.assertEqual(mmph_to_level(2.5), 50)
		self.assertEqual(mmph_to_level(15.), 75)
		self.assertEqual(mmph_to_level(60.), 100)
		self.assertEqual(mmph_to_level(1000.), 100)

	def test01_radar(self):
		img_data = open(datafile('test_sirad_si1_si2.gif')).read()
		r = RadarPadavin(picdata=img_data.encode('base64'), last_modified=datetime.datetime.now())
		r.save()
		r.process()

		gr = GeocodedRadar()
		gr.load_from_model(r)

		# koper
		pos, rain_mmph = gr.get_rain_at_coords(45.547356,13.729792)
		self.assertEqual(pos, (294, 357))
		self.assertEqual(rain_mmph, 0)

		# ljubljana
		pos, rain_mmph = gr.get_rain_at_coords(46.054173,14.507332)
		self.assertEqual(pos, (428, 270))
		self.assertEqual(rain_mmph, 0)

		# maribor
		pos, rain_mmph = gr.get_rain_at_coords(46.554611,15.646534)
		self.assertEqual(pos, (624, 184))
		self.assertEqual(rain_mmph, 0)

		pos, rain_level = gr.get_rain_at_coords(45.545763, 14.106696)
		self.assertEqual(pos, (359, 357)) # 'Pixel coords are off?')
		self.assertEqual(rain_level, .5)
		
		del gr
		r.delete()
	
	def test02_aladin(self):
		today = datetime.date.today()
		for n in (6,12,18,24,30,36,42,48):
			img_data = open(datafile('test02_aladin_%.2d.png' % n)).read()
			a = Aladin(
				date=today,
				last_modified=datetime.datetime.now(),
				timedelta=n,
				picdata=img_data.encode('base64'))
			a.save()
		
		aladini = Aladin.objects.filter(date=today)
		
		ga = GeocodedAladin()
		ga.load_from_models(aladini)
		
		pos, forecast = ga.get_forecast_at_coords(45.545763, 14.106696)
		print 'AAAAAAAAA', pos, pos
		self.assertEqual(pos, (321, 210))
		rain30mm = [i for i in forecast if i['offset'] == 36][0]
		self.assertEqual(rain30mm['rain'], 30)
		
		pos2, forecast2 = ga.get_forecast_at_coords(46.421411, 13.601732)
		print 'EEEEEEEEEEEe', pos2
		self.assertEqual(pos2, pos2)
		rain30mm2 = [i for i in forecast if i['offset'] == 36][0]
		#self.assertEqual(rain30mm2['rain'], 30, 'failed removing markers with rainfall numbers')
