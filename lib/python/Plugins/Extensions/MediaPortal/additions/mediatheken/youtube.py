# -*- coding: utf-8 -*-

import json
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

config_mp.mediaportal.yt_param_regionid_idx = ConfigInteger(default = 2)
config_mp.mediaportal.yt_param_time_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_meta_idx = ConfigInteger(default = 1)
config_mp.mediaportal.yt_paramListIdx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_3d_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_duration_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_video_definition_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_event_types_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_param_video_type_idx = ConfigInteger(default = 0)
config_mp.mediaportal.yt_refresh_token = ConfigText(default="")

APIKEYV3 = mp_globals.yt_a
param_hl = ('&hl=en-US', '&hl=de-DE', '&hl=fr-FR', '&hl=it-IT', '&hl=es-ES', '&hl=pt-PT', '&hl=pl-PL', '&hl=da-DK', '&hl=nb-NO', '&hl=sv-SE', '&hl=fi-FI', '')
param_ajax_hl = ('en','de','fr','it','es','pt','pl','da','no','sv','fi','')
picker_lang = ''
param_ajax_gl = ('us','gb','de','at','ch','fr','it','es','pt','pl','dk','no','se','fi')

agent = getUserAgent()
std_headers = {
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
default_cover = "file://%s/youtube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class youtubeGenreScreen(MenuHelper):
	def __init__(self, session):
		global yt_oauth2

		self.param_qr = ""
		self.param_author = ""
		self.old_mainidx = -1

		self.param_safesearch = ['&safeSearch=none']
		self.subCat = []
		self.subCat_L2 = []

		self.param_time = [
			(_("Date"), "&order=date"),
			(_("Rating"), "&order=rating"),
			(_("Relevance"), "&order=relevance"),
			(_("Title"), "&order=title"),
			(_("Video count"), "&order=videoCount"),
			(_("View count"), "&order=viewCount")
			]

		self.param_metalang = [
			(_('English'), '&relevanceLanguage=en'),
			(_('German'), '&relevanceLanguage=de'),
			(_('French'), '&relevanceLanguage=fr'),
			(_('Italian'), '&relevanceLanguage=it'),
			(_('Spanish'), '&relevanceLanguage=es'),
			(_('Portuguese'), '&relevanceLanguage=pt'),
			(_('Polish'), '&relevanceLanguage=pl'),
			(_('Danish'), '&relevanceLanguage=da'),
			(_('Norwegian'), '&relevanceLanguage=no'),
			(_('Swedish'), '&relevanceLanguage=sv'),
			(_('Finnish'), '&relevanceLanguage=fi'),
			(_('Any'), '')
			]

		self.param_regionid = [
			(_('Whole world'), '&regionCode=US'),
			(_('Great Britain'), '&regionCode=GB'),
			(_('Germany'), '&regionCode=DE'),
			(_('Austria'), '&regionCode=AT'),
			(_('Switzerland'), '&regionCode=CH'),
			(_('France'), '&regionCode=FR'),
			(_('Italy'), '&regionCode=IT'),
			(_('Spain'), '&regionCode=ES'),
			(_('Portugal'), '&regionCode=PT'),
			(_('Poland'), '&regionCode=PL'),
			(_('Denmark'), '&regionCode=DK'),
			(_('Norway'), '&regionCode=NO'),
			(_('Sweden'), '&regionCode=SE'),
			(_('Finland'), '&regionCode=FI')
			]

		self.param_duration = [
			(_('Any'), ''),
			('< 4 Min', '&videoDuration=short'),
			('4..20 Min', '&videoDuration=medium'),
			('> 20 Min', '&videoDuration=long')
			]

		self.param_3d = [
			(_('Any'), ''),
			(_('2D'), '&videoDimension=2d'),
			(_('3D'), '&videoDimension=3d')
			]

		self.param_video_definition = [
			(_('Any'), ''),
			(_('High'), '&videoDefinition=high'),
			(_('Low'), '&videoDefinition=standard')
			]

		self.param_event_types = [
			(_('None'), ''),
			(_('Completed'), '&eventType=completed'),
			(_('Live'), '&eventType=live'),
			(_('Upcoming'), '&eventType=upcoming')
			]

		self.param_video_type = [
			(_('Any'), ''),
			(_('Episode'), '&videoType=episode'),
			(_('Movie'), '&videoType=movie')
			]

		self.paramList = [
			(_('Search request'), (self.paraQuery, None), (0,1,2,)),
			(_('Event type'), (self.param_event_types, config_mp.mediaportal.yt_param_event_types_idx), (0,)),
			(_('Sort by'), (self.param_time, config_mp.mediaportal.yt_param_time_idx), (0,1,2,)),
			(_('Language'), (self.param_metalang, config_mp.mediaportal.yt_param_meta_idx), (0,1,2,7,9,10,11,12,13,14)),
			(_('Search region'), (self.param_regionid, config_mp.mediaportal.yt_param_regionid_idx), (0,1,2,3,7,9,10,11,12,13,14)),
			(_('User name'), (self.paraAuthor, None), (0,1,2,)),
			(_('3D Search'), (self.param_3d, config_mp.mediaportal.yt_param_3d_idx), (0,)),
			(_('Runtime'), (self.param_duration, config_mp.mediaportal.yt_param_duration_idx), (0,)),
			(_('Video definition'), (self.param_video_definition, config_mp.mediaportal.yt_param_video_definition_idx), (0,)),
			(_('Video type'), (self.param_video_type, config_mp.mediaportal.yt_param_video_type_idx), (0,))
			]

		self.subCatUserChannel = [
			(_('Featured'), '/featured?'),
			(_('Videos'), '/videos?'),
			(_('Playlists'), '/playlists?'),
			(_('Channels'), '/channels?')
			]

		self.subCatUserChannelPlaylist = [
			(_('Videos'), '/videos?')
			]

		self.subCatUserChannelPopularWorldwide = [
			(_('Featured'), '/featured?'),
			]

		self.subCatUserChannelPopular = [
			(_('Featured'), '/featured?'),
			(_('Videos'), '/videos?'),
			(_('Playlists'), '/playlists?')
			]

		self.subCatUserChannelPopular2 = [
			(_('Featured'), '/featured?'),
			(_('Videos'), '/videos?')
			]

		self.subCatYourChannel = [
			(_('Playlists'), 'https://www.googleapis.com/youtube/v3/playlists?part=snippet%2Cid&mine=true&access_token=%ACCESSTOKEN%'),
			(_('Uploads'), 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=uploads%'),
			(_('Likes'), 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true&access_token=%ACCESSTOKEN%%playlistId=likes%'),
			(_('Subscriptions'), 'https://www.googleapis.com/youtube/v3/subscriptions?part=snippet&mine=true&access_token=%ACCESSTOKEN%'),
			]

		self.mainGenres = [
			(_('Video search'), 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=video&key=%KEY%'),
			(_('Playlist search'), 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=playlist&key=%KEY%'),
			(_('Channel search'), 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=%QR%&type=channel&key=%KEY%'),
			(_('Trends'), 'https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&key=%KEY%'),
			(400 * "—", ''),
			(_('My channel'), ''),
			(_('Favorites'), ''),
			(_('User Channels'), ''),
			(400 * "—", ''),
			(_('YouTube Channels'), ''),
			(_('Selected Channels'), ''),
			(_('Music Channels'), ''),
			(_('Gaming Channels'), ''),
			(_('Car & Vehicle Channels'), ''),
			(_('Radio Play Channels'), ''),
			]

		self.YTChannels = [
			(_('Popular on YouTube'), 'http://www.youtube.com/channel/UCF0pVplsI8R5kcAqgtoRqoA'),
			(_('News'), 'https://www.youtube.com/channel/UCYfdidRxbB8Qhf0Nx7ioOYw'),
			(_('Music'), 'https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ'),
			(_('Gaming'), 'https://www.youtube.com/channel/UCOpNcN46UbXVtpKMrmU4Abg'),
			(_('Sports'), 'https://www.youtube.com/channel/UCEgdi0XIXXZ-qJOFPf4JSKw'),
			(_('Live'), 'https://www.youtube.com/channel/UC4R8DWoMoI7CAwX8_LjQHig'),
			('YouTube Spotlight', 'https://www.youtube.com/channel/UCBR8-60-B28hp2BmDPdntcQ'),
			('YouTube Trends', 'https://www.youtube.com/channel/UCeNZlh03MyUkjRlLFpVQxsg'),
			('YouTube Creators', 'https://www.youtube.com/channel/UCUZHFZ9jIKrLroW8LcyJEQQ'),
			('YouTube Nation', 'https://www.youtube.com/channel/UCUD4yDVyM54QpfqGJX4S7ng'),
			('YouTube Rewind', 'https://www.youtube.com/channel/UCnHXLLNHjNAnDQ50JANLG1g')
			]

		self.HoerspielChannels = [
			('Audible Deutschland', 'https://www.youtube.com/user/audibletrailer'),
			('Edgar Allan Poe´s Kaminzimmer', 'https://www.youtube.com/user/EAPoeProductions'),
			('FRUITY - SOUND - DISASTER', 'https://www.youtube.com/user/MrFruitylooper'),
			('Hein Bloed', 'https://www.youtube.com/user/Heinbloedful'),
			('Hörspiele und Klassik', 'https://www.youtube.com/user/scyliorhinus'),
			('Lauschgoldladen', 'https://www.youtube.com/user/Lauschgoldladen'),
			('Multipolizei2', 'https://www.youtube.com/user/Multipolizei2'),
			('Multipolizei3', 'https://www.youtube.com/user/Multipolizei3'),
			('Soundtales Productions', 'https://www.youtube.com/user/SoundtalesProduction'),
			]
		self.HoerspielChannels.sort(key=lambda t : t[0].lower())
		self.subCatHoerspielChannels = []
		for item in self.HoerspielChannels:
			self.subCatHoerspielChannels.append(self.subCatUserChannel)

		self.CarChannels = [
			('Alfa Romeo Deutschland', 'https://www.youtube.com/user/AlfaRomeoDE'),
			('Audi Deutschland', 'https://www.youtube.com/user/Audi'),
			('BMW Deutschland', 'https://www.youtube.com/user/BMWDeutschland'),
			('BMW Motorrad', 'https://www.youtube.com/user/bmwmotorrad'),
			('CITROËN Deutschland', 'https://www.youtube.com/user/CitroenDeutschland'),
			('Ducati', 'https://www.youtube.com/user/DucatiMotorHolding'),
			('Fiat Deutschland', 'https://www.youtube.com/user/FiatDeutschland'),
			('Ford Deutschland', 'https://www.youtube.com/user/fordindeutschland'),
			('Harley-Davidson Europe', 'https://www.youtube.com/user/HarleyDavidsonEurope'),
			('Honda Deutschland', 'https://www.youtube.com/user/HondaDeutschlandGmbH'),
			('Kawasaki Motors', 'https://www.youtube.com/user/Kawasakimotors'),
			('Land Rover Deutschland', 'https://www.youtube.com/user/experiencegermany'),
			('Mazda Deutschland', 'https://www.youtube.com/user/MazdaDeutschland'),
			('Mercedes-Benz Deutschland', 'https://www.youtube.com/user/mercedesbenz'),
			('Mitsubishi Motors Europe', 'https://www.youtube.com/channel/UCejAnh9OrFJ_ubho2IIAexQ'),
			('Moto Guzzi', 'https://www.youtube.com/user/motoguzziofficial'),
			('Nissan Deutschland', 'https://www.youtube.com/user/NissanDeutsch'),
			('Porsche', 'https://www.youtube.com/user/Porsche'),
			('SEAT Deutschland', 'https://www.youtube.com/user/SEATde'),
			('ŠKODA AUTO Deutschland', 'https://www.youtube.com/user/skodade'),
			('SUZUKI Way of Life!', 'https://www.youtube.com/user/GlobalSuzukiChannel'),
			('Toyota Deutschland', 'https://www.youtube.com/user/toyota'),
			('Official Triumph Motorcycles', 'https://www.youtube.com/user/OfficialTriumph'),
			('Volkswagen', 'https://www.youtube.com/user/myvolkswagen'),
			('Yamaha Motor Europe', 'https://www.youtube.com/user/YamahaMotorEurope'),
			('AUTO BILD', 'https://www.youtube.com/user/Autobild'),
			('ADAC', 'https://www.youtube.com/user/adac'),
			('MOTORVISION BIKE', 'https://www.youtube.com/user/motorvisionbike'),
			('MOTORRADonline.de', 'https://www.youtube.com/user/motorrad'),
			('TOURENFAHRER', 'https://www.youtube.com/user/Tourenfahrer'),
			('DEKRA Automobil', 'https://www.youtube.com/user/DEKRAAutomobil'),
			('Motorvision', 'https://www.youtube.com/user/MOTORVISIONcom'),
			('auto motor und sport', 'https://www.youtube.com/user/automotorundsport'),
			('1000PS - die starke Motorradseite im Internet', 'https://www.youtube.com/user/1000ps'),
			('Motorrad Online', 'https://www.youtube.com/user/motorrad'),
			('Hyundai Deutschland', 'https://www.youtube.com/user/HyundaiMotorGermany'),
			('Kia Motors Deutschland', 'https://www.youtube.com/user/KiaMotorsDeutschland'),
			]
		self.CarChannels.sort(key=lambda t : t[0].lower())
		self.subCatCarChannels = []
		for item in self.CarChannels:
			self.subCatCarChannels.append(self.subCatUserChannel)

		self.GamingChannels = [
			('THCsGameChannel', 'https://www.youtube.com/user/THCsGameChannel'),
			('GameTube', 'https://www.youtube.com/user/GameTube'),
			('EA - Electronic Arts Deutschland', 'https://www.youtube.com/user/ElectronicArtsDE'),
			('Ubisoft', 'https://www.youtube.com/user/ubisoft'),
			('PlayStation', 'https://www.youtube.com/user/PlayStation'),
			('GameStar', 'https://www.youtube.com/user/GameStarDE'),
			('Assassin\'s Creed DE', 'https://www.youtube.com/user/AssassinsCreedDE'),
			('XboxDACH', 'https://www.youtube.com/user/XboxDE'),
			('GIGA GAMES', 'https://www.youtube.com/user/giga'),
			('Gronkh', 'https://www.youtube.com/user/Gronkh'),
			('Sarazar', 'https://www.youtube.com/user/SarazarLP'),
			('RANDOM ENCOUNTER', 'https://www.youtube.com/user/thegeekmythology'),
			('Game Inside', 'https://www.youtube.com/user/gameinsideshow'),
			('Pink Panter - Comedy', 'https://www.youtube.com/user/WartimeDignity'),
			('Danny Burnage - Darauf ein Snickers-Eis!', 'https://www.youtube.com/user/TheDannyBurnage'),
			('m4xFPS - Keks mit ♥', 'https://www.youtube.com/user/m4xFPS'),
			('xTheSolution', 'https://www.youtube.com/user/xTheSolution'),
			]
		self.GamingChannels.sort(key=lambda t : t[0].lower())
		self.subCatGamingChannels = []
		for item in self.GamingChannels:
			self.subCatGamingChannels.append(self.subCatUserChannel)

		self.MusicChannels = [
			('Ultra Music', 'https://www.youtube.com/user/UltraRecords'),
			('Armada Music', 'https://www.youtube.com/user/armadamusic'),
			('You Love Dance.TV', 'https://www.youtube.com/user/Planetpunkmusic'),
			('Classical Music Only', 'https://www.youtube.com/user/ClassicalMusicOnly'),
			('Music Channel Romania', 'https://www.youtube.com/user/1musicchannel'),
			('50 Cent', 'https://www.youtube.com/user/50CentMusic'),
			('GMC Schlager', 'https://www.youtube.com/user/BlueSilverstar'),
			('Classical Music Channel / Klassische', 'https://www.youtube.com/user/BPanther'),
			('EMI Music Germany', 'https://www.youtube.com/user/EMIMusicGermany'),
			('Sony Music Germany', 'https://www.youtube.com/user/SMECatalogGermany'),
			('MyWorldCharts', 'https://www.youtube.com/user/MyWorldCharts'),
			('CaptainCharts', 'https://www.youtube.com/user/CaptainCharts'),
			('PowerCharts', 'https://www.youtube.com/user/PowerCharts'),
			('Kontor.TV', 'https://www.youtube.com/user/kontor'),
			('Scooter Official', 'https://www.youtube.com/user/scooter'),
			('ATZEN MUSIK TV', 'https://www.youtube.com/user/atzenmusiktv'),
			('BigCityBeats', 'https://www.youtube.com/user/HammerDontHurtEm'),
			('The Best Of', 'https://www.youtube.com/user/alltimebestofmusic'),
			('Tomorrowland', 'https://www.youtube.com/user/TomorrowlandChannel'),
			('►Techno, HandsUp & Dance◄', 'https://www.youtube.com/user/DJFlyBeatMusic'),
			('Zooland Records', 'https://www.youtube.com/user/zoolandMusicGmbH'),
			('Bazooka Records', 'https://www.youtube.com/user/bazookalabel'),
			('Crystal Lake Music', 'https://www.youtube.com/user/CrystaLakeTV'),
			('SKRILLEX', 'https://www.youtube.com/user/TheOfficialSkrillex'),
			('AggroTV', 'https://www.youtube.com/user/aggroTV'),
			('Bands & ART-Psyche', 'https://www.youtube.com/user/thandewye'),
			('Bands & ART-Joint Venture', 'https://www.youtube.com/user/srudlak'),
			('Bands & ART-Madonna', 'https://www.youtube.com/user/madonna'),
			('BB Sound Production', 'https://www.youtube.com/user/b0ssy007'),
			('Chill-out,Lounge,Jazz,Electronic,Psy,Piano,Trance', 'https://www.youtube.com/user/aliasmike2002'),
			('Gothic1', 'https://www.youtube.com/user/AiratzuMusic'),
			('Gothic2', 'https://www.youtube.com/user/INM0R4L'),
			('Gothic-Industrial Mix', 'https://www.youtube.com/user/noetek'),
			('Wave & Gothic', 'https://www.youtube.com/user/MrBelorix'),
			('Indie', 'https://www.youtube.com/user/curie78'),
			('Planetpunkmusic TV', 'https://www.youtube.com/user/Planetpunkmusic'),
			('Selfmade Records', 'https://www.youtube.com/user/SelfmadeRecords'),
			('UKF-DrumandBass', 'https://www.youtube.com/user/UKFDrumandBass'),
			('UKF-Dubstep', 'https://www.youtube.com/user/UKFDubstep'),
			('UKF-Music', 'https://www.youtube.com/user/UKFMusic'),
			('UKF-Mixes', 'https://www.youtube.com/user/UKFMixes'),
			('UKF-Live', 'https://www.youtube.com/user/UKFLive'),
			('Smarty Music', 'https://www.youtube.com/user/smartymcfly'),
			('MoMMusic Network', 'https://www.youtube.com/user/MrMoMMusic'),
			('Schlager Affe', 'https://www.youtube.com/user/schlageraffe2011'),
			('Elvis Presley', 'https://www.youtube.com/user/elvis'),
			('Dj3P51LON', 'https://www.youtube.com/user/Dj3P51LON'),
			('HeadhunterzMedia', 'https://www.youtube.com/user/HeadhunterzMedia'),
			('GMC Volkstümlicher Schlager', 'https://www.youtube.com/user/gusbara'),
			('GMC HQ Volkstümlicher Schlager', 'https://www.youtube.com/user/GMChq'),
			]
		self.MusicChannels.sort(key=lambda t : t[0].lower())
		self.subCatMusicChannels = []
		for item in self.MusicChannels:
			self.subCatMusicChannels.append(self.subCatUserChannel)

		self.SelectedChannels = [
			('VEVO Music', 'https://www.youtube.com/user/VEVO'),
			('KinoCheck', 'https://www.youtube.com/user/KinoCheck'),
			('Rocket Beans TV', 'https://www.youtube.com/user/ROCKETBEANSTV'),
			('Daheimkino', 'https://www.youtube.com/user/Daheimkino'),
			('E2WORLD', 'https://www.youtube.com/channel/UC95hFgcA4hzKcOQHiEFX3UA'),
			('The HDR Channel', 'https://www.youtube.com/channel/UCve7_yAZHFNipzeAGBI5t9g'),
			('4K Relaxation Channel', 'https://www.youtube.com/channel/UCg72Hd6UZAgPBAUZplnmPMQ'),
			('La Belle Musique', 'https://www.youtube.com/user/LaBelleChannel'),
			]
		self.SelectedChannels.sort(key=lambda t : t[0].lower())
		self.subCatSelectedChannels = []
		for item in self.SelectedChannels:
			self.subCatSelectedChannels.append(self.subCatUserChannel)

		try:
			fname = mp_globals.pluginPath + "/resources/userchan.xml"
			self.user_path = config_mp.mediaportal.watchlistpath.value + "mp_userchan.xml"
			from os.path import exists
			if not exists(self.user_path):
				shutil.copyfile(fname, self.user_path)
			fp = open(self.user_path)
			data = fp.read()
			fp.close()
		except IOError, e:
			self.UserChannels = []
			self.UserChannels.append((_('No channels found!'), ''))
		else:
			list = re.findall('<name>(.*?)</name>.*?<user>(.*?)</user>', data, re.S)
			self.UserChannels = []
			if list:
				for (name, user) in list:
					if user.strip().startswith('UC'):
						self.UserChannels.append((name.strip(), 'https://www.youtube.com/channel/'+user.strip()))
					elif user.strip().startswith('PL'):
						self.UserChannels.append((name.strip(), 'gdata.youtube.com/feeds/api/users/'+user.strip()+'/uploads?'))
					else:
						self.UserChannels.append((name.strip(), 'https://www.youtube.com/user/'+user.strip()))
				self.keyLocked = False
			else:
				self.UserChannels.append((_('No channels found!'), ''))
		self.subCatUserChannels = []
		for item in self.UserChannels:
			if item[1].replace('gdata.youtube.com/feeds/api/users/', '').startswith('PL'):
				self.subCatUserChannels.append(self.subCatUserChannelPlaylist)
			elif item[1] != "":
				self.subCatUserChannels.append(self.subCatUserChannel)
			else:
				self.subCatUserChannels.append(None)

		MenuHelper.__init__(self, session, 2, None, "", "", self._defaultlistcenter, 'MP_Plugin', default_cover=default_cover, widgets_files=('MP_widget_youtube',))

		self["yt_actions"] = ActionMap(["MP_Actions"], {
			"yellow": self.keyYellow,
			"blue": self.login
		}, -1)

		self['title'] = Label("YouTube")
		self['ContentTitle'] = Label(_("Genres"))

		self['Query'] = Label(_("Search request"))
		self['query'] = Label()
		self['Time'] = Label(_("Sort by"))
		self['time'] = Label()
		self['Metalang'] = Label(_("Language"))
		self['metalang'] = Label()
		self['Regionid'] = Label(_("Search region"))
		self['regionid'] = Label()
		self['Author'] = Label(_("User name"))
		self['author'] = Label()
		self['Keywords'] = Label(_("Event type"))
		self['keywords'] = Label()
		self['3D'] = Label(_("3D Search"))
		self['3d'] = Label()
		self['Duration'] = Label(_("Runtime"))
		self['duration'] = Label()
		self['Reserve1'] = Label(_("Video definition"))
		self['reserve1'] = Label()
		self['Reserve2'] = Label(_("Video type"))
		self['reserve2'] = Label()

		self['Parameter'] = Label()
		self['Parameter'].hide()

		self['F3'] = Label(_("Edit Parameter"))
		self['F4'] = Label(_("Request YT-Token"))

		self.onLayoutFinish.append(self.initSubCat)
		self.mh_On_setGenreStrTitle.append((self.keyYellow, [0]))
		self.onClose.append(self.saveIdx)

		self.channelId = None

	def initSubCat(self):
		if fileExists("/tmp/mp_yt_cache"):
			tmp = open("/tmp/mp_yt_cache","r")
			data = tmp.read()
			tmp.close()
			self.parseCats(data)
		else:
			hl = 'en-US'
			rc = 'US'
			url = 'https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&hl=%s&regionCode=%s&key=%s' % (hl, rc, APIKEYV3)
			twAgentGetPage(url, agent=agent, headers=std_headers).addCallback(self.parseCats)

	def parseCats(self, data):
		if not fileExists("/tmp/mp_yt_cache"):
			tmp = open("/tmp/mp_yt_cache","w")
			tmp.write(data)
			tmp.close()
		data = json.loads(data)
		strings = [_('Autos & Vehicles'), _('Comedy'), _('Education'), _('Entertainment'), _('Film & Animation'), _('Gaming'), _('Howto & Style'), _('Music'), _('News & Politics'), _('People & Blogs'), _('Pets & Animals'), _('Science & Technology'), _('Sports'), _('Travel & Events')]
		for item in data.get('items', {}):
			if item['snippet']['assignable']:
				self.subCat.append((_(str(item['snippet']['title'].encode('utf-8'))), '&videoCategoryId=%s' % str(item['id'])))
			self.subCat_L2.append(None)
		self.subCat.sort(key=lambda t : t[0].lower())
		self.subCat.insert(0, ((_('No Category'), '')))
		self.subCat_L2.insert(0, (None))

		self.mh_genreMenu = [
			self.mainGenres,
			[
			self.subCat,
			None,
			None,
			None,
			None,
			self.subCatYourChannel,
			None,
			self.UserChannels,
			None,
			self.YTChannels,
			self.SelectedChannels,
			self.MusicChannels,
			self.GamingChannels,
			self.CarChannels,
			self.HoerspielChannels,
			],
			[
			self.subCat_L2,
			None,
			None,
			None,
			None,
			[None, None, None, None],
			None,
			self.subCatUserChannels,
			None,
			[self.subCatUserChannelPopularWorldwide, self.subCatUserChannelPopular2, self.subCatUserChannelPopular2, self.subCatUserChannelPopular2, self.subCatUserChannelPopularWorldwide, self.subCatUserChannelPopularWorldwide, self.subCatUserChannel, self.subCatUserChannelPopular, self.subCatUserChannelPopular, self.subCatUserChannelPopular, self.subCatUserChannelPopular, self.subCatUserChannelPopular],
			self.subCatSelectedChannels,
			self.subCatMusicChannels,
			self.subCatGamingChannels,
			self.subCatCarChannels,
			self.subCatHoerspielChannels,
			]
			]
		self.mh_loadMenu()

	def paraQuery(self):
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True, auto_text_init=True, suggest_func=self.getSuggestions)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			self.showParams()

	def paraAuthor(self):
		self.session.openWithCallback(self.cb_paraAuthor, VirtualKeyBoardExt, title = (_("Author")), text = self.param_author, is_dialog=True)

	def cb_paraAuthor(self, callback = None, entry = None):
		if callback != None:
			self.param_author = callback.strip()
			self.channelId = None
			self.showParams()

	def showParams(self):
		try:
			self['query'].setText(self.param_qr)
			self['time'].setText(self.param_time[config_mp.mediaportal.yt_param_time_idx.value][0])
			self['reserve1'].setText(self.param_video_definition[config_mp.mediaportal.yt_param_video_definition_idx.value][0])
			self['reserve2'].setText(self.param_video_type[config_mp.mediaportal.yt_param_video_type_idx.value][0])
			self['metalang'].setText(self.param_metalang[config_mp.mediaportal.yt_param_meta_idx.value][0])
			self['regionid'].setText(self.param_regionid[config_mp.mediaportal.yt_param_regionid_idx.value][0])
			self['3d'].setText(self.param_3d[config_mp.mediaportal.yt_param_3d_idx.value][0])
			self['duration'].setText(self.param_duration[config_mp.mediaportal.yt_param_duration_idx.value][0])
			self['author'].setText(self.param_author)
			self['keywords'].setText(self.param_event_types[config_mp.mediaportal.yt_param_event_types_idx.value][0])
		except:
			pass

		self.paramShowHide()

	def paramShowHide(self):
		if self.old_mainidx == self.mh_menuIdx[0]:
			return
		else:
			self.old_mainidx = self.mh_menuIdx[0]

		showCtr = 0
		if self.mh_menuIdx[0] in self.paramList[0][2]:
			self['query'].show()
			self['Query'].show()
			showCtr = 1
		else:
			self['query'].hide()
			self['Query'].hide()

		if self.mh_menuIdx[0] in self.paramList[1][2]:
			self['keywords'].show()
			self['Keywords'].show()
			showCtr = 1
		else:
			self['keywords'].hide()
			self['Keywords'].hide()

		if self.mh_menuIdx[0] in self.paramList[2][2]:
			self['time'].show()
			self['Time'].show()
			showCtr = 1
		else:
			self['time'].hide()
			self['Time'].hide()

		if self.mh_menuIdx[0] in self.paramList[3][2]:
			self['metalang'].show()
			self['Metalang'].show()
			showCtr = 1
		else:
			self['metalang'].hide()
			self['Metalang'].hide()

		if self.mh_menuIdx[0] in self.paramList[4][2]:
			self['regionid'].show()
			self['Regionid'].show()
			showCtr = 1
		else:
			self['regionid'].hide()
			self['Regionid'].hide()

		if self.mh_menuIdx[0] in self.paramList[5][2]:
			self['author'].show()
			self['Author'].show()
			showCtr = 1
		else:
			self['author'].hide()
			self['Author'].hide()

		if self.mh_menuIdx[0] in self.paramList[6][2]:
			self['3d'].show()
			self['3D'].show()
			showCtr = 1
		else:
			self['3d'].hide()
			self['3D'].hide()

		if self.mh_menuIdx[0] in self.paramList[7][2]:
			self['duration'].show()
			self['Duration'].show()
			showCtr = 1
		else:
			self['duration'].hide()
			self['Duration'].hide()

		if self.mh_menuIdx[0] in self.paramList[8][2]:
			self['reserve1'].show()
			self['Reserve1'].show()
			showCtr = 1
		else:
			self['reserve1'].hide()
			self['Reserve1'].hide()

		if self.mh_menuIdx[0] in self.paramList[9][2]:
			self['reserve2'].show()
			self['Reserve2'].show()
			showCtr = 1
		else:
			self['reserve2'].hide()
			self['Reserve2'].hide()

		if showCtr:
			self['F3'].show()
		else:
			self['F3'].hide()

	def mh_loadMenu(self):
		self.showParams()
		self.mh_setMenu(0, True)
		self.mh_keyLocked = False

	def keyYellow(self, edit=1):
		c = len(self.paramList)
		list = []
		if config_mp.mediaportal.yt_paramListIdx.value not in range(0, c):
			config_mp.mediaportal.yt_paramListIdx.value = 0
		old_idx = config_mp.mediaportal.yt_paramListIdx.value
		for i in range(c):
			if self.mh_menuIdx[0] in self.paramList[i][2]:
				list.append((self.paramList[i][0], i))

		if list and edit:
			self.session.openWithCallback(self.cb_handlekeyYellow, ChoiceBoxExt, title=_("Edit Parameter"), list = list, selection=old_idx)
		else:
			self.showParams()

	def cb_handlekeyYellow(self, answer):
		pidx = answer and answer[1]
		if pidx != None:
			config_mp.mediaportal.yt_paramListIdx.value = pidx
			if type(self.paramList[pidx][1][0]) == list:
				self.changeListParam(self.paramList[pidx][0], *self.paramList[pidx][1])
			else:
				self.paramList[pidx][1][0]()
		self.showParams()

	def changeListParam(self, nm, l, idx):
		if idx.value not in range(0, len(l)):
			idx.value = 0

		list = []
		for i in range(len(l)):
			list.append((l[i][0], (i, idx)))

		if list:
			self.session.openWithCallback(self.cb_handleListParam, ChoiceBoxExt, title=_("Edit Parameter") + " '%s'" % nm, list = list, selection=idx.value)

	def cb_handleListParam(self, answer):
		p = answer and answer[1]
		if p != None:
			p[1].value = p[0]
			self.showParams()

	def getUserChannelId(self, usernm, callback):
		url = 'https://www.googleapis.com/youtube/v3/channels?part=id&forUsername=%s&key=%s' % (usernm, APIKEYV3)
		twAgentGetPage(url, agent=agent, headers=std_headers).addCallback(self.parseChannelId).addCallback(lambda x: callback()).addErrback(self.parseChannelId, True)

	def parseChannelId(self, data, err=False):
		try:
			data = json.loads(data)
			self.channelId = str(data['items'][0]['id'])
		except:
			printl('No CID found.',self,'E')
			self.channelId = 'none'

	def openListScreen(self):
		tm = self.param_time[config_mp.mediaportal.yt_param_time_idx.value][1]
		lr = self.param_metalang[config_mp.mediaportal.yt_param_meta_idx.value][1]
		regionid = self.param_regionid[config_mp.mediaportal.yt_param_regionid_idx.value][1]
		_3d = self.param_3d[config_mp.mediaportal.yt_param_3d_idx.value][1]
		dura = self.param_duration[config_mp.mediaportal.yt_param_duration_idx.value][1]
		vid_def = self.param_video_definition[config_mp.mediaportal.yt_param_video_definition_idx.value][1]
		event_type = self.param_event_types[config_mp.mediaportal.yt_param_event_types_idx.value][1]

		genreurl = self.mh_genreUrl[0] + self.mh_genreUrl[1]
		if 'googleapis.com' in genreurl:
			if '/playlists' in genreurl:
				lr = param_hl[config_mp.mediaportal.yt_param_meta_idx.value]

			if not '%ACCESSTOKEN%' in genreurl:
				if self.param_author:
					if not self.channelId:
						return self.getUserChannelId(self.param_author, self.openListScreen)
					else:
						channel_id = '&channelId=%s' % self.channelId
				else: channel_id = ''
				genreurl = genreurl.replace('%QR%', urllib.quote_plus(self.param_qr))
				genreurl += regionid + lr + tm + channel_id + self.param_safesearch[0]
				if 'type=video' in genreurl:
					vid_type = self.param_video_type[config_mp.mediaportal.yt_param_video_type_idx.value][1]
					genreurl += _3d + dura + vid_def + event_type + vid_type

		elif _('Favorites') in self.mh_genreTitle:
			genreurl = ''
		else:
			genreurl = self.mh_genreUrl[0] + self.mh_genreUrl[1] + self.mh_genreUrl[2]

		if self.mh_genreTitle != (400 * "—"):
			self.session.open(YT_ListScreen, genreurl, self.mh_genreTitle)

	def mh_callGenreListScreen(self):
		global picker_lang
		picker_lang = ''
		if _('My channel') in self.mh_genreTitle:
			if not config_mp.mediaportal.yt_refresh_token.value:
				self.session.open(MessageBoxExt, _("You need to request a token to allow access to your YouTube account."), MessageBoxExt.TYPE_INFO)
				return
		self.openListScreen()

	def login(self):
		if not config_mp.mediaportal.yt_refresh_token.value:
			yt_oauth2.requestDevCode(self.session)
		else:
			self.session.openWithCallback(self.cb_login, MessageBoxExt, _("Did you revoke the access?"), type=MessageBoxExt.TYPE_YESNO, default=False)

	def cb_login(self, answer):
		if answer is True:
			yt_oauth2.requestDevCode(self.session)

	def saveIdx(self):
		config_mp.mediaportal.yt_param_time_idx.save()
		config_mp.mediaportal.yt_param_meta_idx.save()
		config_mp.mediaportal.yt_param_regionid_idx.save()
		configfile_mp.save()
		yt_oauth2._tokenExpired()

	def getSuggestions(self, text, max_res):
		hl = param_ajax_hl[config_mp.mediaportal.yt_param_meta_idx.value]
		gl = param_ajax_gl[config_mp.mediaportal.yt_param_regionid_idx.value]
		url = "https://clients1.google.com/complete/search?client=youtube&hl=%s&gl=%s&ds=yt&q=%s" % (hl, gl, urllib.quote_plus(text))
		d = twAgentGetPage(url, agent=agent, headers=std_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and suggestions:
			i=suggestions.find(',[["')
			if i > 0:
				for m in re.finditer('"(.+?)",0', suggestions[i:]):
					list.append(decodeHtml(m.group(1)))
					max_res -= 1
					if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class YT_ListScreen(MPScreen, ThumbsHelper):

	param_regionid = (
		('&gl=US'),
		('&gl=GB'),
		('&gl=DE'),
		('&gl=AT'),
		('&gl=CH'),
		('&gl=FR'),
		('&gl=IT'),
		('&gl=ES'),
		('&gl=PT'),
		('&gl=PL'),
		('&gl=DK'),
		('&gl=NO'),
		('&gl=SE'),
		('&gl=FI')
		)

	def __init__(self, session, stvLink, stvGenre, title="YouTube"):
		self.stvLink = stvLink
		self.genreName = stvGenre
		self.headers = std_headers

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self.favoGenre = self.genreName.startswith(_('Favorites'))
		self.apiUrl = 'youtube.com' in self.stvLink
		self.apiUrlv3 = 'googleapis.com' in self.stvLink
		self.ajaxUrl = '/c4_browse_ajax' in self.stvLink
		self.c4_browse_ajax = ''
		self.url_c4_browse_ajax_list = ['']

		self["actions"]  = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok" 		: self.keyOK,
			"red"		: self.keyRed,
			"cancel"	: self.keyCancel,
			"5" 		: self.keyShowThumb,
			"up" 		: self.keyUp,
			"down" 		: self.keyDown,
			"right" 	: self.keyRight,
			"left" 		: self.keyLeft,
			"upUp" 		: self.key_repeatedUp,
			"rightUp" 	: self.key_repeatedUp,
			"leftUp" 	: self.key_repeatedUp,
			"downUp" 	: self.key_repeatedUp,
			"upRepeated"	: self.keyUpRepeated,
			"downRepeated"	: self.keyDownRepeated,
			"rightRepeated"	: self.keyRightRepeated,
			"leftRepeated"	: self.keyLeftRepeated,
			"nextBouquet"	: self.keyPageUpFast,
			"prevBouquet"	: self.keyPageDownFast,
			"green"		: self.keyGreen,
			"0"		: self.closeAll,
			"1" 		: self.key_1,
			"3" 		: self.key_3,
			"4" 		: self.key_4,
			"6" 		: self.key_6,
			"7" 		: self.key_7,
			"9" 		: self.key_9
		}, -1)

		self['title'] = Label(title)

		self['ContentTitle'] = Label(self.genreName)
		if not self.favoGenre:
			self['F2'] = Label(_("Favorite"))
		else:
			self['F2'] = Label(_("Delete"))

		if ('order=' in self.stvLink) and ('type=video' in self.stvLink) or (self.apiUrl and '/uploads' in self.stvLink):
			self['F1'] = Label(_("Sort by"))
			self.key_sort = True
		else:
			self.key_sort = False

		self['Page'] = Label(_("Page:"))

		self['coverArt'].hide()
		self.coverHelper = CoverHelper(self['coverArt'])
		self.propertyImageUrl = None
		self.keyLocked = True
		self.baseUrl = "https://www.youtube.com"
		self.lastUrl = None

		self.setVideoPrio()

		self.favo_path = config_mp.mediaportal.watchlistpath.value + "mp_yt_favorites.xml"
		self.keckse = CookieJar()
		self.filmliste = []
		self.start_idx = 1
		self.max_res = 50
		self.max_pages = 1000 / self.max_res
		self.total_res = 0
		self.pages = 0
		self.page = 0
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.load_more_href = None
		self.onClose.append(self.youtubeExit)
		self.modeShowThumb = 1
		self.playAll = True
		self.showCover = False
		self.lastCover = ""
		self.actType = None
		self.mine = False

		if not self.apiUrl:
			self.onLayoutFinish.append(self.loadPageData)
		else:
			self.onLayoutFinish.append(self.checkAPICallv2)

	def checkAPICallv2(self):
		m = re.search('/api/users/(.*?)/uploads\?', self.stvLink, re.S)
		if not m:
			m = re.search('/user/(.*?)/videos\?$', self.stvLink, re.S)
		if not m:
			m = re.search('/channel/(.*?)/videos\?$', self.stvLink, re.S)
		if m:
			if m.group(1).startswith('PL'):
				self.stvLink = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&order=date&playlistId=%s&key=%s" % (m.group(1), APIKEYV3)
				self.apiUrl = False
				self.apiUrlv3 = True
			elif not m.group(1).startswith('UC'):
				url = 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forUsername=%s&key=%s' % (m.group(1), APIKEYV3)
				return twAgentGetPage(url, agent=agent, headers=self.headers).addCallback(self.parsePlaylistId).addErrback(self.dataError)
			else:
				self.apiUrl = False
				self.apiUrlv3 = True
				self.stvLink = 'https://www.googleapis.com/youtube/v3/search?part=snippet&order=date&channelId=%s&key=%s' % (m.group(1), APIKEYV3)

		reactor.callLater(0, self.loadPageData)

	def parsePlaylistId(self, data):
		data = json.loads(data)
		try:
			plid = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
		except:
			printl('No PLID found.',self,'E')
		else:
			self.stvLink = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&order=date&playlistId=%s&key=%s' % (str(plid), APIKEYV3)
			self.apiUrl = False
			self.apiUrlv3 = True

		reactor.callLater(0, self.loadPageData)

	def loadPageData(self):
		if _('No channels found!') in self.genreName:
			self.close()
			return
		self.keyLocked = True
		self.ml.setList(map(self.YT_ListEntry, [(_('Please wait...'),'','','','','','')]))
		hl = param_ajax_hl[config_mp.mediaportal.yt_param_meta_idx.value]
		if hl != picker_lang:
			self.setLang("https://www.youtube.com", hl)
			return

		if self.favoGenre:
			self.getFavos()
		else:
			url = self.stvLink
			if self.apiUrlv3:
				url = url.replace('%KEY%', APIKEYV3)
				url += "&maxResults=%d" % (self.max_res,)
				if self.c4_browse_ajax:
					url += '&pageToken=' + self.c4_browse_ajax
			elif self.ajaxUrl:
				if not 'paging=' in url:
					url += '&paging=%d' % max(1, self.page)
				url = '%s%s' % (self.baseUrl, url)
			elif self.c4_browse_ajax:
				url = '%s%s' % (self.baseUrl, self.c4_browse_ajax)
			else:
				if url[-1] == '?' or url[-1] == '&':
					url = '%sflow=list' % url
				elif url[-1] != '?' or url[-1] != '&':
					url = '%s&flow=list' % url
				if not '&gl=' in url:
					url += self.param_regionid[config_mp.mediaportal.yt_param_regionid_idx.value]

			self.lastUrl = url
			if self.apiUrlv3 and '%ACT-' in url:
				self.actType = re.search('(%ACT-.*?%)', url).group(1)
				url = url.replace(self.actType, '', 1)
				self.actType = unicode(re.search('%ACT-(.*?)%', self.actType).group(1))

			if '%ACCESSTOKEN%' in url:
				token = yt_oauth2.getAccessToken()
				if not token:
					yt_oauth2.refreshToken(self.session).addCallback(self.getData, url).addErrback(self.dataError)
				else:
					self.getData(token, url)
			else:
				self.getData(None, url)

	def setLang(self, url, hl):
		picker_url = "https://www.youtube.com/picker_ajax?action_language=1&base_url=" + urllib.quote(url)
		twAgentGetPage(picker_url, cookieJar=self.keckse, agent=agent, headers=self.headers).addCallback(self.gotPickerData, hl).addErrback(self.dataError)

	def gotPickerData(self, data, hl):
		global picker_lang
		try:
			data = json.loads(data)["html"].encode('utf-8')
			m = re.search('<form(.*?)</form>', data, re.S)
			action_url = self.baseUrl + re.search('action="(.*?)"', m.group(1)).group(1).replace('&amp;', '&')
			base_url = re.search('<input.*?name="base_url" value="(.*?)"', m.group(1)).group(1).replace('&amp;', '&')
			session_token = re.search('<input.*?name="session_token" value="(.*?)"', m.group(1)).group(1)
		except:
			print 'html:',data
		else:
			picker_lang = hl
			postdata = urllib.urlencode({
				'base_url': base_url,
				'session_token': session_token,
				'hl': hl})
			headers = self.headers.copy()
			headers['Content-Type'] = 'application/x-www-form-urlencoded'
			twAgentGetPage(action_url, method='POST', cookieJar=self.keckse, agent=agent, headers=headers, postdata=postdata).addCallback(lambda _: self.loadPageData()).addErrback(self.pickerError)

	def pickerError(self, err):
		printl('pickerError:%s' % err,self,'E')

	def getData(self, token, url):
		if token:
			url = url.replace('%ACCESSTOKEN%', token, 1)
			if '%playlistId=' in url:
				return self.getRelatedUserPL(url, token)
		if "&mine=true" in url:
			self.mine = True
		else:
			self.mine = False
		#printl(url,self,'I')
		twAgentGetPage(url, cookieJar=self.keckse, agent=agent, headers=self.headers).addCallback(self.genreData).addErrback(self.dataError)

	def getRelatedUserPL(self, url, token):
		pl = re.search('%playlistId=(.*?)%', url).group(1)
		yt_url = re.sub('%playlistId=.*?%', '', url, 1)
		twAgentGetPage(yt_url, cookieJar=self.keckse, agent=agent, headers=self.headers).addCallback(self.parseRelatedPL, token, pl).addErrback(self.dataError)

	def parseRelatedPL(self, data, token, pl):
		try:
			data = json.loads(data)
		except:
			pass
		else:
			for item in data.get('items', {}):
				playlist = item['contentDetails']['relatedPlaylists']
				if pl in playlist:
					yt_url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&access_token=%s&order=date' % (str(playlist[pl]), token)
					yt_url += "&maxResults=%d" % (self.max_res,)
					if self.c4_browse_ajax:
						yt_url += '&pageToken=' + self.c4_browse_ajax
					#printl(yt_url,self,'I')
					return twAgentGetPage(yt_url, cookieJar=self.keckse, agent=agent, headers=self.headers).addCallback(self.genreData).addErrback(self.dataError)

		reactor.callLater(0, genreData, '')

	def parsePagingUrl(self, data):
		regex = re.compile('data-uix-load-more-href="(.*?)"')
		m = regex.search(data)
		if m:
			if not self.page:
				self.page = 1
			self.c4_browse_ajax = m.group(1).replace('&amp;', '&')
		else:
			if not 'load-more-text' in data:
				self.c4_browse_ajax = ''
				self.pages = self.page

	def parsePagingUrlv3(self, jdata):
		if not self.page:
			self.page = 1
		self.c4_browse_ajax = str(jdata.get('nextPageToken', ''))

	def convertDuration(self, duration):
		date = ':' + duration.replace('P', '').replace('W', '-').replace('D', ' ').replace('T', '').replace('H', ':').replace('M', ':').replace('S', '')
		if 'S' not in duration:
			date += '00'
		elif date[-2] == ':':
			date = date[:-1] + '0' + date[-1]
		if 'M' not in duration:
			date = date[:-2] + '00' + date[-3:]
		elif date[-5] == ':':
			date = date[:-4] + '0' + date[-4:]
		return date[1:]

	def genreData(self, data):
		if ("quotaExceeded" in data) or ("dailyLimitExceeded" in data):
			global APIKEYV3
			if APIKEYV3 != mp_globals.yt_a_backup:
				APIKEYV3 = mp_globals.yt_a_backup
				self.ml.setList(map(self.YT_ListEntry, [('',_('We switched to our API backup key, please try again!'),'','','','','')]))
			else:
				self.ml.setList(map(self.YT_ListEntry, [('',_('Our YouTube API quota exceeded, try again tomorrow!'),'','','','','')]))
			self['handlung'].setText("")
			self.keyLocked = True
		else:
			if self.apiUrlv3:
				data = json.loads(data)
				self.parsePagingUrlv3(data)

			elif not self.apiUrl:
				try:
					if "load_more_widget_html" in data:
						data = json.loads(data)
						self.parsePagingUrl(data["load_more_widget_html"].replace("\\n","").replace("\\","").encode('utf-8'))
						data = data["content_html"].replace("\\n","").replace("\\","").encode('utf-8')
					else:
						data = json.loads(data)["content_html"].replace("\\n","").replace("\\","").encode('utf-8')
						self.parsePagingUrl(data)
				except:
					self.parsePagingUrl(data)

			elif not self.pages:
				m = re.search('totalResults>(.*?)</', data)
				if m:
					a = int(m.group(1))
					self.pages = a // self.max_res
					if a % self.max_res:
						self.pages += 1
					if self.pages > self.max_pages:
						self.pages = self.max_pages
					self.page = 1

			self.filmliste = []
			if self.apiUrlv3:
				def getThumbnail(thumbnails):
					if 'maxres' in thumbnails:
						return str(thumbnails['maxres']['url'])
					elif 'medium' in thumbnails:
						return str(thumbnails['medium']['url'])
					elif 'standard' in thumbnails:
						return str(thumbnails['standard']['url'])
					elif 'high' in thumbnails:
						return str(thumbnails['high']['url'])
					else:
						return str(thumbnails['default']['url'])

				listType = re.search('ItemList|subscriptionList|activityList|playlistList|CategoryList|channelList|videoListResponse', data.get('kind', '')) != None
				runtimeurl = 'https://www.googleapis.com/youtube/v3/videos?key=%KEY%&part=contentDetails,snippet,statistics&id='
				runtimeurl = runtimeurl.replace('%KEY%', APIKEYV3)
				for item in data.get('items', []):
					if not listType:
						try:
							kind = item['id'].get('kind')
						except:
							continue
					else:
						try:
							kind = item.get('kind')
						except:
							continue

					if kind != None:
						if item.has_key('snippet'):
							if kind.endswith('#video'):
								try:
									runtimeurl = runtimeurl + str(item['id']['videoId']) + ","
								except:
									try:
										runtimeurl = runtimeurl + str(item['id']) + ","
									except:
										continue
							elif kind.endswith('#playlistItem'):
								try:
									runtimeurl = runtimeurl + str(item['snippet']['resourceId']['videoId']) + ","
								except:
									continue

				if not runtimeurl.endswith('&id='):
					runtimedata = ''
					try:
						import requests
						s = requests.session()
						page = s.get(runtimeurl.strip(','))
						runtimedata = json.loads(page.content)
					except:
						pass

				for item in data.get('items', []):
					if not listType:
						try:
							kind = item['id'].get('kind')
						except:
							continue
					else:
						try:
							kind = item.get('kind')
						except:
							continue
					if kind != None:
						if item.has_key('snippet'):
							localized = item['snippet'].has_key('localized')
							if not localized:
								title = decodeHtml(str(item['snippet'].get('title', '')))
								desc = str(item['snippet'].get('description', ''))
							else:
								loca = item['snippet']['localized']
								title = decodeHtml(str(loca.get('title', '')))
								desc = str(loca.get('description', ''))
							if kind.endswith('#video'):
								try:
									url = str(item['id']['videoId'])
									img = getThumbnail(item['snippet']['thumbnails'])
								except:
									try:
										url = str(item['id'])
										img = getThumbnail(item['snippet']['thumbnails'])
									except:
										continue
								desc = "\n" + desc
								try:
									for runitem in runtimedata.get('items', []):
										runtime = ''
										if str(runitem["id"]) == url:
											views = str(runitem["statistics"]["viewCount"])
											runtime = self.convertDuration(str(runitem["contentDetails"]["duration"]))
											if runtime == "00:00":
												runtime = "live"
											if runtime != "live":
												desc = _("Views:") + " " + views + "\n" + desc
											desc = _("Runtime:") + " " + runtime + "\n" + desc
											break
								except:
									pass
								try:
									date = re.findall('(\d{4})-(\d{2})-(\d{2})T(.*?).000Z', str(item['snippet'].get('publishedAt', '')))
									date = date[0][2] + "." + date[0][1] + "." + date[0][0] + ", " + date[0][3]
									desc = _("Published:") + " " + date + "\n" + desc
								except:
									pass
								channel = str(item['snippet'].get('channelTitle', ''))
								desc = _("Channel:") + " " + channel + "\n" + desc
								self.filmliste.append(('', title, url, img, desc, '', ''))
							elif kind.endswith('#playlistItem'):
								try:
									url = str(item['snippet']['resourceId']['videoId'])
									img = getThumbnail(item['snippet']['thumbnails'])
								except:
									continue
								desc = "\n" + desc
								try:
									for runitem in runtimedata.get('items', []):
										runtime = ''
										if str(runitem["id"]) == url:
											views = str(runitem["statistics"]["viewCount"])
											runtime = self.convertDuration(str(runitem["contentDetails"]["duration"]))
											if runtime == "00:00":
												runtime = "live"
											if runtime != "live":
												desc = _("Views:") + " " + views + "\n" + desc
											desc = _("Runtime:") + " " + runtime + "\n" + desc
											break
								except:
									pass
								try:
									date = re.findall('(\d{4})-(\d{2})-(\d{2})T(.*?).000Z', str(item['snippet'].get('publishedAt', '')))
									date = date[0][2] + "." + date[0][1] + "." + date[0][0] + ", " + date[0][3]
									desc = _("Published:") + " " + date + "\n" + desc
								except:
									pass
								channel = str(item['snippet'].get('channelTitle', ''))
								desc = _("Channel:") + " " + channel + "\n" + desc
								self.filmliste.append(('', title, url, img, desc, '', ''))
							elif kind.endswith('channel'):
								if listType:
									id = str(item['id'])
									url = '/channel/%s/featured' % id
									img = getThumbnail(item['snippet']['thumbnails'])
									self.filmliste.append(('', title, url, img, desc, '', ''))
								else:
									url = str(item['id']['channelId'])
									img = getThumbnail(item['snippet']['thumbnails'])
									self.filmliste.append(('', title, url, img, desc, 'CV3', ''))
							elif kind.endswith('#playlist'):
								if not listType:
									url = str(item['id']['playlistId'])
								else:
									url = str(item['id'])
								img = getThumbnail(item['snippet']['thumbnails'])
								self.filmliste.append(('', title, url, img, desc, 'PV3', ''))
							elif kind.endswith('#subscription'):
								url = str(item['snippet']['resourceId']['channelId'])
								img = getThumbnail(item['snippet']['thumbnails'])
								self.filmliste.append(('', title, url, img, desc, 'CV3', ''))
							elif kind.endswith('#guideCategory'):
								url = str(item['id'])
								img = ''
								self.filmliste.append(('', title, url, img, desc, 'GV3', ''))
							elif kind.endswith('#activity'):
								desc = str(item['snippet'].get('description', ''))
								if item['snippet'].get('type') == self.actType:
									try:
										if self.actType == u'upload':
											url = str(item['contentDetails'][self.actType]['videoId'])
										else:
											url = str(item['contentDetails'][self.actType]['resourceId']['videoId'])
										img = getThumbnail(item['snippet']['thumbnails'])
									except:
										pass
									else:
										self.filmliste.append(('', title, url, img, desc, '', ''))
						elif 'contentDetails' in item:
							details = item['contentDetails']
							if kind.endswith('#channel'):
								if 'relatedPlaylists' in details:
									for k, v in details['relatedPlaylists'].iteritems:
										url = str(v)
										img = ''
										desc = ''
										self.filmliste.append(('', str(k).title(), url, img, desc, 'PV3', ''))

			else:
				data = data.replace('\n', '')
				entrys = None
				list_item_cont = branded_item = shelf_item = yt_pl_thumb = list_item = pl_video_yt_uix_tile = yt_lockup_video = False
				if self.genreName.endswith("Channels") and "branded-page-related-channels-item" in data:
					branded_item = True
					entrys = data.split("branded-page-related-channels-item")
				elif "channels-browse-content-list-item" in data:
					list_item = True
					entrys = data.split("channels-browse-content-list-item")
				elif "browse-list-item-container" in data:
					list_item_cont = True
					entrys = data.split("browse-list-item-container")
				elif re.search('[" ]+shelf-item[" ]+', data):
					shelf_item = True
					entrys = data.split("shelf-item ")
				elif "yt-pl-thumb " in data:
					yt_pl_thumb = True
					entrys = data.split("yt-pl-thumb ")
				elif "pl-video yt-uix-tile " in data:
					pl_video_yt_uix_tile = True
					entrys = data.split("pl-video yt-uix-tile ")
				elif "yt-lockup-video " in data:
					yt_lockup_video = True
					entrys = data.split("yt-lockup-video ")

				if entrys and not self.propertyImageUrl:
					m = re.search('"appbar-nav-avatar" src="(.*?)"', entrys[0])
					property_img = m and m.group(1)
					if property_img:
						if property_img.startswith('//'):
							property_img = 'http:' + property_img
						self.propertyImageUrl = property_img

				if list_item_cont or branded_item or shelf_item or list_item or yt_pl_thumb or pl_video_yt_uix_tile or yt_lockup_video:
					for entry in entrys[1:]:

						if 'data-item-type="V"' in entry:
							vidcnt = '[Paid Content] '
						elif 'data-title="[Private' in entry:
							vidcnt = '[private Video] '
						else:
							vidcnt = ''

						gid = 'S'
						m = re.search('href="(.*?)" class=', entry)
						vid = m and m.group(1).replace('&amp;','&')
						if not vid:
							continue
						if branded_item and not '/SB' in vid:
							continue

						img = title = ''
						if '<span class="" ' in entry:
							m = re.search('<span class="" .*?>(.*?)</span>', entry)
							if m:
								title += decodeHtml(m.group(1))
						elif 'dir="ltr" title="' in entry:
							m = re.search('dir="ltr" title="(.+?)"', entry, re.S)
							if m:
								title += decodeHtml(m.group(1).strip())
							m = re.search('data-thumb="(.*?)"', entry)
							img = m and m.group(1)
						else:
							m = re.search('dir="ltr".*?">(.+?)</a>', entry, re.S)
							if m:
								title += decodeHtml(m.group(1).strip())
							m = re.search('data-thumb="(.*?)"', entry)
							img = m and m.group(1)

						if not img:
							img = self.propertyImageUrl

						if img and img.startswith('//'):
							img = 'http:' + img
						img = img.replace('&amp;','&')

						desc = ''
						if not vidcnt and 'list=' in vid and not '/videos?' in self.stvLink:
							m = re.search('formatted-video-count-label">\s+<b>(.*?)</b>', entry)
							if m:
								vidcnt = '[%s Videos] ' % m.group(1)
						elif vid.startswith('/watch?'):
							if not vidcnt:
								vid = re.search('v=(.+)', vid).group(1)
								gid = ''
								m = re.search('video-time">(.+?)<', entry)
								if m:
									dura = m.group(1)
									if len(dura)==4:
										vtim = '0:0%s' % dura
									elif len(dura)==5:
											vtim = '0:%s' % dura
									else:
										vtim = dura
									vidcnt = '[%s] ' % vtim

							m = re.search('data-name=.*?>(.*?)</.*?<li>(.*?)</li>\s+</ul>', entry)
							if m:
								desc += 'von ' + decodeHtml(m.group(1)) + ' · ' + m.group(2).replace('</li>', ' ').replace('<li>', '· ') + '\n'

						m = re.search('class="yt-lockup-description.*?dir="ltr">(.*?)</div>', entry)

						if (shelf_item or list_item_cont) and not desc and not m:
							m = re.search('shelf-description.*?">(.+?)</div>', entry)

						if m:
							desc += decodeHtml(m.group(1).strip())
							splits = desc.split('<br />')
							desc = ''
							for split in splits:
								if not '<a href="' in split:
									desc += split + '\n'

						if list_item and not vidcnt:
							m = re.search('yt-lockup-meta-info"><li>(.*?)</ul>', entry)
							if m:
								vidcnt = re.sub('<.*?>', '', m.group(1))
								vidcnt = '[%s] ' % vidcnt

						self.filmliste.append((vidcnt, str(title), vid, img, desc, gid, ''))

			reactor.callLater(0, self.checkListe)

	def checkListe(self):
		if len(self.filmliste) == 0:
			self.filmliste.append(('',_('No contents / results found!'),'','','','',''))
			self.keyLocked = True
			if self.page <= 1:
				self.page = 0
			self.pages = self.page
			self.c4_browse_ajax = ''
		else:
			if not self.page:
				self.page = self.pages = 1
			menu_len = len(self.filmliste)
			self.keyLocked = False

		self.ml.setList(map(self.YT_ListEntry, self.filmliste))
		self.th_ThumbsQuery(self.filmliste, 1, 2, 3, None, None, self.page, self.pages, mode=self.modeShowThumb)
		self.showInfos()

	def dataError(self, error):
		self.keyLocked = True
		self.ml.setList(map(self.YT_ListEntry, [('',_('No contents / results found!'),'','','','','')]))
		self['handlung'].setText("")

	def showInfos(self):
		if (self.c4_browse_ajax and not self.pages) and self.page:
			self['page'].setText("%d" % self.page)
		else:
			self['page'].setText("%d / %d" % (self.page,max(self.page, self.pages)))

		stvTitle = self['liste'].getCurrent()[0][1]
		stvImage = self['liste'].getCurrent()[0][3]
		desc = self['liste'].getCurrent()[0][4]
		self['name'].setText(stvTitle)
		self['handlung'].setText(desc)
		if self.lastCover != stvImage:
			self.lastCover = stvImage
			stvImage = stvImage.replace('s240-c-k', 's900-c-k').replace('s100-c-k', 's900-c-k').replace('s88-c-k', 's900-c-k')
			stvImage = stvImage.replace('s240-nd-c', 's900-nd-c').replace('s100-nd-c', 's900-nd-c').replace('s88-nd-c', 's900-nd-c')
			stvImage = stvImage.replace('s240-mo-c', 's900-mo-c').replace('s100-mo-c', 's900-mo-c').replace('s88-mo-c', 's900-mo-c')
			self.coverHelper.getCover(stvImage)

	def youtubeErr(self, error):
		self['handlung'].setText(_("Unfortunately, this video can not be played!\n")+str(error))

	def setVideoPrio(self):
		self.videoPrio = int(config_mp.mediaportal.youtubeprio.value)

	def delFavo(self):
		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.filmliste)
		try:
			f1 = open(self.favo_path, 'w')
			while j < l:
				if j != i:
					c += 1
					dura = self.filmliste[j][0]
					dhTitle = self.filmliste[j][1]
					dhVideoId = self.filmliste[j][2]
					dhImg = self.filmliste[j][3]
					desc = urllib.quote(self.filmliste[j][4])
					gid = self.filmliste[j][5]
					wdat = '<i>%d</i><n>%s</n><v>%s</v><im>%s</im><d>%s</d><g>%s</g><desc>%s</desc>\n' % (c, dhTitle, dhVideoId, dhImg, dura, gid, desc)
					f1.write(wdat)

				j += 1

			f1.close()
			self.getFavos()

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def addFavo(self):
		dhTitle = self['liste'].getCurrent()[0][1]
		dura = self['liste'].getCurrent()[0][0]
		dhImg = self['liste'].getCurrent()[0][3]
		gid = self['liste'].getCurrent()[0][5]
		desc = urllib.quote(self['liste'].getCurrent()[0][4])
		dhVideoId = self['liste'].getCurrent()[0][2]
		if not self.favoGenre and gid in ('S','P','C'):
			dura = ''
			dhTitle = self.genreName + ':' + dhTitle

		try:
			if not fileExists(self.favo_path):
				f1 = open(self.favo_path, 'w')
				f_new = True
			else:
				f_new = False
				f1 = open(self.favo_path, 'a+')

			max_i = 0
			if not f_new:
				data = f1.read()
				for m in re.finditer('<i>(\d*?)</i>.*?<v>(.*?)</v>', data):
					v_found = False
					i, v = m.groups()
					ix = int(i)
					if ix > max_i:
						max_i = ix
					if v == dhVideoId:
						v_found = True
					if v_found:
						f1.close()
						self.session.open(MessageBoxExt, _("Favorite already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
						return

			wdat = '<i>%d</i><n>%s</n><v>%s</v><im>%s</im><d>%s</d><g>%s</g><desc>%s</desc>\n' % (max_i + 1, dhTitle, dhVideoId, dhImg, dura, gid, desc)
			f1.write(wdat)
			f1.close()
			self.session.open(MessageBoxExt, _("Favorite added"), MessageBoxExt.TYPE_INFO, timeout=5)

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def getFavos(self):
		self.filmliste = []
		try:
			if not fileExists(self.favo_path):
				f_new = True
			else:
				f_new = False
				f1 = open(self.favo_path, 'r')

			if not f_new:
				data = f1.read()
				f1.close()
				for m in re.finditer('<n>(.*?)</n><v>(.*?)</v><im>(.*?)</im><d>(.*?)</d><g>(.*?)</g><desc>(.*?)</desc>', data):
					n, v, img, dura, gid, desc = m.groups()
					if dura and not dura.startswith('['):
						dura = '[%s] ' % dura.rstrip()
					self.filmliste.append((dura, n, v, img, urllib.unquote(desc), gid, ''))

			if len(self.filmliste) == 0:
				self.pages = self.page = 0
				self.filmliste.append((_('No videos found!'),'','','','','',''))
				self.keyLocked = True
				if not f_new and len(data) > 0:
					os.remove(self.favo_path)

			else:
				self.pages = self.page = 1
				self.keyLocked = False

			self.ml.setList(map(self.YT_ListEntry, self.filmliste))
			self.showInfos()

		except IOError, e:
			print "Fehler:\n",e
			print "eCode: ",e
			self['handlung'].setText(_("Error!\n")+str(e))
			f1.close()

	def changeSort(self):
		list = (
			(_("Date"), ("order=date", 0)),
			(_("Rating"), ("order=rating", 1)),
			(_("Relevance"), ("order=relevance", 2)),
			(_("Title"), ("order=title", 3)),
			(_("Video count"), ("order=videoCount", 4)),
			(_("View count"), ("order=viewCount", 5))
			)
		self.session.openWithCallback(self.cb_handleSortParam, ChoiceBoxExt, title=_("Sort by"), list = list, selection=config_mp.mediaportal.yt_param_time_idx.value)

	def cb_handleSortParam(self, answer):
		p = answer and answer[1]
		if p != None:
			config_mp.mediaportal.yt_param_time_idx.value = p[1]
			self.stvLink = re.sub('order=([a-zA-Z]+)', p[0], self.stvLink)
			self.keckse.clear()
			self.c4_browse_ajax = ''
			self.url_c4_browse_ajax_list = ['']
			self.page = self.pages = 0
			self.loadPageData()

	def keyRed(self):
		if not self.key_sort:
			return
		elif not self.keyLocked:
			self.changeSort()

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.showInfos()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyUp(self):
		if self.keyLocked:
			return
		i = self['liste'].getSelectedIndex()
		if not i:
			self.keyPageDownFast()

		self['liste'].up()
		self.showInfos()

	def keyDown(self):
		if self.keyLocked:
			return
		i = self['liste'].getSelectedIndex()
		l = len(self.filmliste) - 1
		if l == i:
			self.keyPageUpFast()

		self['liste'].down()
		self.showInfos()

	def keyTxtPageUp(self):
		if self.keyLocked:
			return
		self['handlung'].pageUp()

	def keyTxtPageDown(self):
		if self.keyLocked:
			return
		self['handlung'].pageDown()

	def keyPageUpFast(self,step=1):
		if self.keyLocked:
			return
		oldpage = self.page
		if not self.c4_browse_ajax and not self.apiUrlv3:
			if not self.page or not self.pages:
				return
			if (self.page + step) <= self.pages:
				self.page += step
				self.start_idx += self.max_res * step
			else:
				self.page = 1
				self.start_idx = 1
		elif self.c4_browse_ajax:
			self.url_c4_browse_ajax_list.append(self.c4_browse_ajax)
			self.page += 1
		else:
			return

		if oldpage != self.page:
			self.loadPageData()

	def keyPageDownFast(self,step=1):
		if self.keyLocked:
			return
		oldpage = self.page
		if not self.c4_browse_ajax and not self.apiUrlv3:
			if not self.page or not self.pages:
				return
			if (self.page - step) >= 1:
				self.page -= step
				self.start_idx -= self.max_res * step
			else:
				self.page = self.pages
				self.start_idx = self.max_res * (self.pages - 1) + 1
		else:
			if self.page <= 1:
				return
			self.url_c4_browse_ajax_list.pop()
			self.c4_browse_ajax = self.url_c4_browse_ajax_list[-1]
			self.page -= 1

		if oldpage != self.page:
			self.loadPageData()

	def key_1(self):
		self.keyPageDownFast(2)

	def keyGreen(self):
		if self.keyLocked:
			return
		if self.favoGenre:
			self.delFavo()
		else:
			self.addFavo()

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][2]
		gid = self['liste'].getCurrent()[0][5]
		if gid == 'P' or gid == 'C':
			dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			if genreurl.startswith('http'):
				genreurl = genreurl.replace('v=2', '')
			else:
				genreurl = 'gdata.youtube.com/feeds/api/playlists/'+self['liste'].getCurrent()[0][2]+'?'
				dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'CV3':
			dhTitle = 'Ergebnisse: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			genreurl = 'https://www.googleapis.com/youtube/v3/search?part=snippet%2Cid&type=video&order=date&channelId='+self['liste'].getCurrent()[0][2]+'&key=%KEY%'

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'GV3':
			dhTitle = 'Ergebnisse: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			hl = param_hl[config_mp.mediaportal.yt_param_meta_idx.value]
			genreurl = 'https://www.googleapis.com/youtube/v3/channels?part=snippet&categoryId='+self['liste'].getCurrent()[0][2]+hl+'&key=%KEY%'

			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif gid == 'PV3':
			dhTitle = 'Videos: ' + self['liste'].getCurrent()[0][1]
			genreurl = self['liste'].getCurrent()[0][2]
			genreurl = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&order=date&playlistId='+self['liste'].getCurrent()[0][2]
			if config_mp.mediaportal.yt_refresh_token.value and self.mine:
				genreurl = genreurl + '&access_token=%ACCESSTOKEN%'
			else:
				genreurl = genreurl + '&key=%KEY%'
			if self.favoGenre:
				self.session.openWithCallback(self.getFavos, YT_ListScreen, genreurl, dhTitle)
			else:
				self.session.open(YT_ListScreen, genreurl, dhTitle)
		elif not self.apiUrl or gid == 'S':
			global picker_lang
			if url.startswith('/playlist?'):
				m = re.search('list=(.+)', url)
				if m:
					url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&order=date&key=' % m.group(1)
					url += '%KEY%'
					dhTitle = 'Playlist: ' + self['liste'].getCurrent()[0][1]
					self.session.open(YT_ListScreen, url, dhTitle)
			elif url.startswith('/user/') or url.startswith('/channel/'):
				url = url.replace('&amp;', '&')
				if '?' in url:
					url += '&'
				else:
					url += '?'
				url =  self.baseUrl + url
				dhTitle = self.genreName + ':' + self['liste'].getCurrent()[0][1]
				picker_lang = ''
				self.session.open(YT_ListScreen, url, dhTitle)
			elif url.startswith('/watch?v='):
				if not 'list=' in url or '/videos?' in self.stvLink:
					url = re.search('v=(.+)', url).group(1)
					listitem = self.filmliste[self['liste'].getSelectedIndex()]
					liste = [(listitem[0], listitem[1], url, listitem[3], listitem[4], listitem[5], listitem[6])]
					self.session.openWithCallback(
						self.setVideoPrio,
						YoutubePlayer,
						liste,
						0,
						playAll = False,
						listTitle = self.genreName,
						plType='local',
						title_inr=1,
						showCover=self.showCover
						)
				else:
					url = re.search('list=(.+)', url).group(1)
					url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=%s&order=date&key=' % url
					url += '%KEY%'
					dhTitle = 'Playlist: ' + self['liste'].getCurrent()[0][1]
					self.session.open(YT_ListScreen, url, dhTitle)
			else:
				self.session.openWithCallback(
					self.setVideoPrio,
					YoutubePlayer,
					self.filmliste,
					self['liste'].getSelectedIndex(),
					playAll = self.playAll,
					listTitle = self.genreName,
					plType='local',
					title_inr=1,
					showCover=self.showCover
					)
		elif not self['liste'].getCurrent()[0][6]:
			self.session.openWithCallback(
				self.setVideoPrio,
				YoutubePlayer,
				self.filmliste,
				self['liste'].getSelectedIndex(),
				playAll = self.playAll,
				listTitle = self.genreName,
				plType='local',
				title_inr=1,
				showCover=self.showCover
				)

	def youtubeExit(self):
		self.keckse.clear()
		del self.filmliste[:]

class YT_Oauth2:
	OAUTH2_URL = 'https://accounts.google.com/o/oauth2'
	CLIENT_ID = mp_globals.yt_i
	CLIENT_SECRET = mp_globals.yt_s
	SCOPE = '&scope=https://www.googleapis.com/auth/youtube'
	GRANT_TYPE = '&grant_type=http://oauth.net/grant_type/device/1.0'
	TOKEN_PATH = '/etc/enigma2/mp_yt-access-tokens.json'
	accessToken = None

	def __init__(self):
		import os.path
		self._interval = None
		self._code = None
		self._expiresIn = None
		self._refreshTimer = None
		self.autoRefresh = False
		self.abortPoll = False
		self.waitingBox = None
		self.session = None
		if not config_mp.mediaportal.yt_refresh_token.value:
			self._recoverToken()

	def _recoverToken(self):
		if os.path.isfile(self.TOKEN_PATH):
			with open(self.TOKEN_PATH) as data_file:
				data = json.load(data_file)
				config_mp.mediaportal.yt_refresh_token.value = data['refresh_token'].encode('utf-8')
				config_mp.mediaportal.yt_refresh_token.save()
				configfile_mp.save()
				return True

	def requestDevCode(self, session):
		self.session = session
		postData = self.CLIENT_ID + self.SCOPE
		twAgentGetPage(self.OAUTH2_URL+'/device/code', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_requestDevCode, False).addErrback(self._cb_requestDevCode)

	def _cb_requestDevCode(self, data, error=True):
		if error:
			self.session.open(MessageBoxExt, _("Error: Unable to request the Device code"), MessageBoxExt.TYPE_ERROR)
			printl(_("Error: Unable to request the Device code"),self,'E')
		else:
			googleData = json.loads(data)
			self._interval = googleData['interval']
			self._code = '&code=%s' % googleData['device_code'].encode('utf-8')
			self._expiresIn = googleData['expires_in']
			self.session.openWithCallback(self.cb_request, MessageBoxExt, _("You've to visit:\n{url}\nand enter the code: {code}\nCancel action?").format(url=googleData["verification_url"].encode('utf-8'), code=googleData["user_code"].encode('utf-8')), type = MessageBoxExt.TYPE_YESNO, default = False)

	def cb_request(self, answer):
		if answer is False:
			self.waitingBox = self.session.openWithCallback(self.cb_cancelPoll, MessageBoxExt, _("Waiting for response from the server.\nCancel action?"), type = MessageBoxExt.TYPE_YESNO, default = True, timeout = self._expiresIn - 30)
			self.abortPoll = False
			reactor.callLater(self._interval, self._pollOauth2Server)

	def cb_cancelPoll(self, answer):
		if answer is True:
			self.abortPoll = True

	def _pollOauth2Server(self):
		self._tokenExpired()
		postData = self.CLIENT_ID + self.CLIENT_SECRET + self._code + self.GRANT_TYPE
		twAgentGetPage(self.OAUTH2_URL+'/token', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_poll, False).addErrback(self._cb_poll)

	def _cb_poll(self, data, error=True):
		if error:
			self.waitingBox.cancel()
			self.session.open(MessageBoxExt, _('Error: Unable to get tokens!'), MessageBoxExt.TYPE_ERROR)
			printl(_('Error: Unable to get tokens!'),self,'E')
		else:
			try:
				tokenData = json.loads(data)
			except:
				self.waitingBox.cancel()
				self.session.open(MessageBoxExt, _('Error: Unable to get tokens!'), MessageBoxExt.TYPE_ERROR)
				printl('json data error:%s' % str(data),self,'E')
			else:
				if not tokenData.get('error',''):
					self.accessToken = tokenData['access_token'].encode('utf-8')
					config_mp.mediaportal.yt_refresh_token.value = tokenData['refresh_token'].encode('utf-8')
					config_mp.mediaportal.yt_refresh_token.value = tokenData['refresh_token'].encode('utf-8')
					config_mp.mediaportal.yt_refresh_token.save()
					configfile_mp.save()
					self._expiresIn = tokenData['expires_in']
					self._startRefreshTimer()
					f = open(self.TOKEN_PATH, 'w')
					f.write(json.dumps(tokenData))
					f.close()
					self.waitingBox.cancel()
					self.session.open(MessageBoxExt, _('Access granted :)\nFor safety you should create backup\'s of enigma2 settings and \'/etc/enigma2/mp_yt-access-tokens.json\'.\nThe tokens are valid until they are revoked in Your Google Account.'), MessageBoxExt.TYPE_INFO)
				elif not self.abortPoll:
					print tokenData.get('error','').encode('utf-8')
					reactor.callLater(self._interval, self._pollOauth2Server)

	def refreshToken(self, session, skip=False):
		self.session = session
		if not skip:
			self._tokenExpired()
		if config_mp.mediaportal.yt_refresh_token.value:
			postData = self.CLIENT_ID + self.CLIENT_SECRET + '&refresh_token=%s&grant_type=refresh_token' % config_mp.mediaportal.yt_refresh_token.value

			d = twAgentGetPage(self.OAUTH2_URL+'/token', method='POST', postdata=postData, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self._cb_refresh, False).addErrback(self._cb_refresh)
			return d

	def _cb_refresh(self, data, error=True):
		if error:
			printl(_('Error: Unable to refresh token!'),self,'E')
			return data
		else:
			try:
				tokenData = json.loads(data)
				self.accessToken = tokenData['access_token'].encode('utf-8')
				self._expiresIn = tokenData['expires_in']
			except:
				printl('json data error!',self,'E')
				return ""
			else:
				self._startRefreshTimer()
				return self.accessToken

	def revokeToken(self):
		if config_mp.mediaportal.yt_refresh_token.value:
			twAgentGetPage(self.OAUTH2_URL+'/revoke?token=%s' % config_mp.mediaportal.yt_refresh_token.value).addCallback(self._cb_revoke, False).addErrback(self._cb_revoke)

	def _cb_revoke(self, data, error=True):
		if error:
			printl('Error: Unable to revoke!',self,'E')

	def _startRefreshTimer(self):
		if self._refreshTimer != None and self._refreshTimer.active():
			self._refreshTimer.cancel()
		self._refreshTimer = reactor.callLater(self._expiresIn - 10, self._tokenExpired)

	def _tokenExpired(self):
		if self._refreshTimer != None and self._refreshTimer.active():
			self._refreshTimer.cancel()
		self._expiresIn = 0
		self.accessToken = None

	def getAccessToken(self):
		if self.accessToken == None:
			return ""
		else:
			return self.accessToken

yt_oauth2 = YT_Oauth2()