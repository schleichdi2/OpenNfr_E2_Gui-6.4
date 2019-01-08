# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
import mp_globals
from debuglog import printlog as printl
from keyboardext import VirtualKeyBoardExt
from coverhelper import CoverHelper
from youtubeplayer import YoutubePlayer
from Components.ProgressBar import ProgressBar

api_key = mp_globals.bdmt

class MediaPortalTmdbScreen(MPScreen):

	def __init__(self, session, movie_title):
		self.session = session
		self.movie_title = movie_title
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"]  = ActionMap(["MP_Actions"], {
			"ok": self.keyOk,
			"cancel": self.cancel,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"green" : self.keyGreen
		}, -1)

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self['title'] = Label("TMDb - The Movie Database")
		self['name'] = Label("")
		self['ContentTitle'] = Label()
		self['F1'] = Label("")
		self['F2'] = Label(_("Edit"))
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['Page'] = Label("")
		self['page'] = Label("")
		self['coverArt'] = Pixmap()

		self.onLayoutFinish.append(self.tmdbSearch)

	def tmdbSearch(self):
		self.filmliste = []
		self['name'].setText(_("Trying to find results for \"%s\" in TMDb...") % self.movie_title)
		url = "http://api.themoviedb.org/3/search/movie?api_key=%s&query=%s&language=%s" % (api_key, self.movie_title.replace(' ','%20'), "de")
		getPage(url).addCallback(self.getResults).addErrback(self.dataError)

	def getResults(self, data):
		res = json.loads(data)
		for node in res["results"]:
			cover = str(node["poster_path"])
			id = str(node["id"])
			otitle = str(node["original_title"])
			title = str(node["title"])
			url_cover = "http://image.tmdb.org/t/p/original%s" % cover
			url = "http://api.themoviedb.org/3/movie/%s?api_key=%s&append_to_response=releases,trailers,casts&language=%s" % (id, api_key, "de")
			type = _("Movie")
			self.filmliste.append((title, url_cover, url, id, type, 'movie'))
		url = "http://api.themoviedb.org/3/search/tv?api_key=%s&query=%s&language=%s" % (api_key, self.movie_title.replace(' ','%20'), "de")
		getPage(url).addCallback(self.getResults2).addErrback(self.dataError)

	def getResults2(self, data):
		res = json.loads(data)
		for node in res["results"]:
			cover = str(node["poster_path"])
			id = str(node["id"])
			otitle = str(node["original_name"])
			title = str(node["name"])
			url_cover = "http://image.tmdb.org/t/p/original%s" % cover
			url = "http://api.themoviedb.org/3/tv/%s?api_key=%s&append_to_response=releases,trailers,casts&language=%s" % (id, api_key, "de")
			type = _("TV Show")
			self.filmliste.append((title, url_cover, url, id, type, 'tv'))
		self.ml.setList(map(self.movielist, self.filmliste))
		if len(self.filmliste) > 0:
			self['name'].setText(_("Results for \"%s\"") % self.movie_title)
			self.showInfos()
		else:
			self['name'].setText(_("No results found for \"%s\"") % self.movie_title)

	def showInfos(self):
		url_cover = self['liste'].getCurrent()[0][1]
		CoverHelper(self['coverArt']).getCover(url_cover)

	def dataError(self, error):
		from debuglog import printlog as printl
		printl(error,self,"E")

	def keyOk(self):
		check = self['liste'].getCurrent()
		if check == None:
			return
		title =  self['liste'].getCurrent()[0][0]
		cover = self['liste'].getCurrent()[0][1]
		url = self['liste'].getCurrent()[0][2]
		id = self['liste'].getCurrent()[0][3]
		type = self['liste'].getCurrent()[0][5]
		self.session.open(MediaPortaltmdbScreenMovie, title, url, cover, id, type)

	def keyLeft(self):
		check = self['liste'].getCurrent()
		if check == None:
			return
		self['liste'].pageUp()
		self.showInfos()

	def keyRight(self):
		check = self['liste'].getCurrent()
		if check == None:
			return
		self['liste'].pageDown()
		self.showInfos()

	def keyDown(self):
		check = self['liste'].getCurrent()
		if check == None:
			return
		self['liste'].down()
		self.showInfos()

	def keyUp(self):
		check = self['liste'].getCurrent()
		if check == None:
			return
		self['liste'].up()
		self.showInfos()

	def keyGreen(self):
		self.session.openWithCallback(self.goSearch, VirtualKeyBoardExt, title = (_("Search:")), text = self.movie_title, is_dialog=True)

	def goSearch(self, newTitle):
		if newTitle is not None:
			self.movie_title = newTitle
			self.tmdbSearch()
		else:
			self.tmdbSearch()

	def exit(self, which):
		if which:
			self.cancel()
		else:
			self.keyGreen()

	def cancel(self):
		self.close()

	def movielist(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 160, 0, width - 110, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

class MediaPortaltmdbScreenMovie(MPScreen):

	def __init__(self, session, mname, url, cover, id, type):
		self.session = session
		self.mname = mname
		self.url = url
		self.cover = cover
		self.id = id
		self.type = type
		MPScreen.__init__(self, session, skin='MP_TMDb')

		self["actions"]  = ActionMap(["MP_Actions"], {
			"cancel": self.cancel,
			"yellow": self.keyYellow,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"up"    : self.keyLeft,
			"down"  : self.keyRight
		}, -1)

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		self.trailer = None

		self['title'] = Label("TMDb - The Movie Database")

		self['searchinfo'] = Label()
		self['genre'] = Label("-")
		self['genre_txt'] = Label(_("Genre:"))
		self['fulldescription'] = ScrollLabel("")
		self['rating_txt'] = Label(_("Rating:"))
		self['rating'] = Label("")
		self['votes'] = Label("")
		self['votes_txt'] = Label(_("Votes:"))
		self['runtime'] = Label("-")
		self['runtime_txt'] = Label(_("Runtime:"))
		self['fsk'] = Label()
		self['fsk_txt'] = Label(_("Rated:"))
		self['subtitle'] = Label()
		self['year'] = Label("-")
		self['year_txt'] = Label(_("Year:"))
		self['country'] = Label("-")
		self['country_txt'] = Label(_("Countries:"))
		self['director'] = Label("-")
		self['director_txt'] = Label(_("Director:"))
		self['author'] = Label("-")
		self['author_txt'] = Label(_("Author:"))
		self['studio'] = Label("-")
		self['studio_txt'] = Label(_("Studio:"))
		self['F1'] = Label()
		self['F2'] = Label()
		self['F3'] = Label()
		self['F4'] = Label()
		self['coverArt'] = Pixmap()
		self['rating10'] = ProgressBar()
		self['rating0'] = Pixmap()

		self.onLayoutFinish.append(self.onFinish)

	def onFinish(self):
		self['rating10'].setValue(0)
		self.urlfsk = "https://altersfreigaben.de/api/tmdb_id/"+str(self.id)
		getPage(self.urlfsk).addCallback(self.getDataFSK).addErrback(self.dataError)
		self['searchinfo'].setText(_('Loading information for "%s"') % self.mname)
		getPage(self.url).addCallback(self.getData).addErrback(self.dataError)
		CoverHelper(self['coverArt']).getCover(self.cover)

	def getDataFSK(self, data):
		# https://altersfreigaben.de/api/tmdb_id/000(Die Nullen sind durch die enstprechende ID zu ersetzen)
		# Antwort:
		# 0 - Freigegeben ab 0
		# 6 - Freigegeben ab 6
		# 12 - Freigegeben ab 12
		# 16 - Freigegeben ab 16
		# 18 - Freigegeben 18
		# 100 - Film nicht in der Datenbank vorhanden
		# 200 - Der Film wurde (noch) nicht von der FSK eingestuft
		# 300 - Falsches Format der übergebenen ID
		json_data = json.loads(data)
		try:
			if json_data <=99:
				self['fsk'].setText(str(json_data))
			else:
				self['fsk'].setText("-")
		except:
			self['fsk'].setText("-")

	def getData(self, data):
		json_data = json.loads(data)

		try:
			if json_data['release_date']:
				year = json_data['release_date'][:+4]
				self['searchinfo'].setText("%s" % self.mname)
				self['year'].setText("%s" % str(year))
		except:
			try:
				if json_data['first_air_date']:
					year = json_data['first_air_date'][:+4]
					self['year'].setText("%s" % str(year))
				if json_data['last_air_date']:
					lastyear = json_data['last_air_date'][:+4]
					if lastyear != year:
						year = "%s-%s" % (str(year), str(lastyear))
						self['year'].setText(year)
				self['searchinfo'].setText("%s" % self.mname)
			except:
				pass

		vote_average = ""
		if json_data['vote_average']:
			vote_average = json_data['vote_average']
			self['rating'].setText("%s" % str(vote_average))
			rating = int(float(vote_average)*10)
			if rating > 100:
				rating = 100
			self['rating10'].setValue(rating)

		vote_count = ""
		if json_data['vote_count']:
			vote_count = json_data['vote_count']
			self['votes'].setText("%s" % str(vote_count))

		try:
			runtime = ""
			if json_data['runtime']:
				runtime = json_data['runtime']
				self['runtime'].setText("%s min." % str(runtime))
				runtime = ", " + str(runtime) + " min."
		except:
			runtime = ""
			if json_data['episode_run_time']:
				runtime = json_data['episode_run_time'][0]
				self['runtime'].setText("%s min." % str(runtime))
				runtime = ", " + str(runtime) + " min."

		try:
			country_string = ""
			if json_data['production_countries']:
				for country in json_data['production_countries']:
					country_string += country['iso_3166_1']+"/"
				country_string = country_string[:-1]
				self['country'].setText("%s" % str(country_string))
		except:
			country_string = ""
			if json_data['origin_country']:
				for country in json_data['origin_country']:
					country_string += country+"/"
				country_string = country_string[:-1]
				self['country'].setText("%s" % str(country_string))

		genre_string = ""
		if json_data['genres']:
			genre_count = len(json_data['genres'])
			for genre in json_data['genres']:
				genre_string += genre['name']+", "
			self['genre'].setText("%s" % str(genre_string[:-2]))

		try:
			subtitle = ""
			if json_data['tagline']:
				subtitle = json_data['tagline']
				self['subtitle'].setText("%s" % str(subtitle))
				subtitle = str(subtitle) + "\n"
		except:
			pass

		try:
			cast_string = ""
			if json_data['casts']['cast']:
				for cast in json_data['casts']['cast']:
					cast_string += cast['name']+" ("+ cast['character'] + ")\n"
		except:
			pass

		try:
			crew_string = ""
			director = ""
			author = ""
			if json_data['casts']['crew']:
				for crew in json_data['casts']['crew']:
					crew_string += crew['name']+" ("+ crew['job'] + ")\n"

					if crew['job'] == "Director":
						director += crew['name']+", "
					if crew['job'] == "Screenplay" or crew['job'] == "Writer":
						author += crew['name']+", "
				director = director[:-2]
				author = author[:-2]
				self['director'].setText("%s" % str(director))
				self['author'].setText("%s" % str(author))
		except:
			try:
				if json_data['created_by']:
					for crew in json_data['created_by']:
						author += crew['name']+", "
					author = author[:-2]
					self['author'].setText("%s" % str(author))
			except:
				pass
		try:
			studio_string = ""
			if json_data['production_companies']:
				for studio in json_data['production_companies']:
					studio_string += studio['name'] +", "
				studio_string = studio_string[:-2]
				self['studio'].setText("%s" % str(studio_string))
		except:
			pass

		description = ""
		if json_data['overview']:
			description = json_data['overview']
			description = description + "\n\n" + cast_string + "\n" + crew_string
			movieinfo ="%s%s %s%s" % (str(genre_string), str(country_string), str(year), str(runtime))
			fulldescription = movieinfo + "\n\n" + description
			self['fulldescription'].setText("%s" % fulldescription.encode('utf_8','ignore'))

		try:
			if json_data['trailers']['youtube']:
				for trailer in json_data['trailers']['youtube']:
					y_url = str(trailer['source'])
					self['F3'].setText("Trailer")
					self.trailer = y_url
					break
			else:
				print "[TMDb] no trailer found !"
		except:
			pass

	def dataError(self, error):
		from debuglog import printlog as printl
		printl(error,self,"E")

	def keyLeft(self):
		self['fulldescription'].pageUp()

	def keyRight(self):
		self['fulldescription'].pageDown()

	def keyYellow(self):
		if self.trailer:
			self.session.open(YoutubePlayer,[(self.mname, self.trailer, None)],playAll= False,showPlaylist=False,showCover=False)

	def cancel(self):
		self.close()