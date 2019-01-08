from . import xmltvconverter, mp_epg
SimpleEPG = mp_epg.SimpleEPG
mpepg = mp_epg.mpepg

def epg_test():
	mpepg.storeEPGData()
	if mpepg.has_epg:
		events=mpepg.getEvent('rtl.ch')
		if events:
			ch, now, next = events
			print 'now: %s %s - %s' % (ch,time.strftime('%X',time.localtime(now[0])),now[2])
			if next:
				print 'next: %s %s - %s' % (ch,time.strftime('%X',time.localtime(next[0])),next[2])

