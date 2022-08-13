#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import os
import sys
import json
import dateutil.parser
import babel
from flask import (
  Flask, render_template, request, Response, flash,
  redirect, url_for, abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Artist, Show, Venue, Availability
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
  # date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  recent_artists = Artist.query.all()
  recent_venues = Venue.query.all()

  return render_template(
    'pages/home.html',
    recent_artists=reversed(recent_artists),
    recent_venues=reversed(recent_venues)
  )


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  state_city = {(v.city, v.state): [] for v in venues}

  for v in venues:
    state_city[(v.city, v.state)].append(v)

  data = []
  for k, v in state_city.items():
    d = {}
    d['city'] = k[0]
    d['state'] = k[1]
    d['venues'] = v
    data.append(d)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(venues),
    "data": venues
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get_or_404(venue_id)
  upcoming_shows = []
  past_shows = []
  all_shows = db.session.\
    query(Show).\
    join(Venue.shows).\
    filter_by(venue_id=venue_id).all()

  for show in all_shows:
    temp_show = {
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time
    }

    if show.start_time <= datetime.now():
      past_shows.append(temp_show)
    else:
      upcoming_shows.append(temp_show)

  data = vars(venue)
  data['upcoming_shows'] = upcoming_shows
  data['past_shows'] = past_shows
  data['upcoming_shows_count'] = len(upcoming_shows)
  data['past_shows_count'] = len(past_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm(request.form, meta={'csrf': False})
  
  if form.validate():
    venue = Venue(
        name=form.name.data,
        address=form.address.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        website=form.website_link.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description=form.seeking_description.data,
        genres=form.genres.data
      )

    try:
      db.session.add(venue)
      db.session.commit()
    except:
      # when there is any error from the db
      # sets the error flag
      error = True
      db.session.rollback()
      print(sys.exc_info())
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))

    flash('Errors ' + str(message))
    return render_template('forms/new_venue.html', form=form)

  # on successful db insert, flash success
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')

  return redirect(url_for('index'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue Successfully Deleted!')
  except:
    flash(f'Failed to Delete Venue with id: {venue_id}!')
    db.session.rollback()
  finally:
    db.session.close()

  if error:
    response = {
      'status': 'success',
      'redirect_url': 'http://127.0.0.1:5000/'
    }
  else:
    response = {
      'status': 'failed',
      'redirect_url': 'http://127.0.0.1:5000/'
    }

  return response

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  data = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  form = AvailabilityForm()
  artist = Artist.query.get_or_404(artist_id)
  upcoming_shows = []
  past_shows = []
  all_shows = db.session.\
    query(Show).\
    join(Artist.shows).\
    filter_by(artist_id=artist_id).all()

  for show in all_shows:
    temp_show = {
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time
    }
    if show.start_time <= datetime.now():
      past_shows.append(temp_show)
    else:
      upcoming_shows.append(temp_show)

  data = vars(artist)
  data['upcoming_shows'] = upcoming_shows
  data['past_shows'] = past_shows
  data['upcoming_shows_count'] = len(upcoming_shows)
  data['past_shows_count'] = len(past_shows)

  return render_template('pages/show_artist.html', artist=data, form=form)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if not artist:
    abort(404)

  # TODO: populate form with fields from artist with ID <artist_id>
  form.name.data = artist.name
  form.phone.data = artist.phone
  form.city.data = artist.city
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get_or_404(artist_id)
  
  artist.name = form.name.data
  artist.phone = form.phone.data
  artist.city = form.city.data
  artist.website_link = form.website_link.data
  artist.facebook_link = form.facebook_link.data
  artist.seeking_venue = form.seeking_venue.data
  artist.seeking_description = form.seeking_description.data
  artist.image_link = form.image_link.data
  artist.state = form.state.data
  artist.genres = form.genres.data

  try:
    db.session.commit()
    flash('Artist Updated Successfully')
  except:
    db.session.rollback()
    flash('Failed to Update Artist!')
    print(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if not venue:
    abort(404)

  # TODO: populate form with values from venue with ID <venue_id>
  form.name.data = venue.name
  form.address.data = venue.address
  form.city.data = venue.city
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  form.genres.data = [(genre, genre) for genre in venue.genres]

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(request.form)

  venue.name = form.name.data
  venue.address = form.address.data
  venue.city = form.city.data
  venue.state = form.state.data
  venue.phone = form.phone.data
  venue.website = form.website_link.data
  venue.facebook_link = form.facebook_link.data
  venue.image_link = form.image_link.data
  venue.seeking_talent = form.seeking_talent.data
  venue.seeking_description = form.name.data
  venue.genres = form.genres.data
    
  try:
    db.session.commit()
    flash('Venue Updated Successfully')
  except:
    db.session.rollback()
    flash('Failed to Update Venue')
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))
  
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  artist = Artist(
    name=form.name.data,
    phone=form.phone.data,
    city=form.city.data,
    state=form.state.data,
    facebook_link=form.facebook_link.data,
    image_link=form.image_link.data,
    website=form.website_link.data,
    seeking_venue=form.seeking_venue.data,
    seeking_description=form.seeking_description.data,
    genres=form.genres.data
  )
  


  try:
    # on successful db insert, flash success
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  
  data = []
  all_shows = Show.query.all()
  for show in all_shows:
      show_venue = Venue.query.get_or_404(show.venue_id)
      show_artist = Artist.query.get_or_404(show.artist_id)
        
#         populating shows with real data from the database
      data.append(
            {
        "venue_id": show_venue.id,
        "venue_name": show_venue.name,
        "artist_id": show_artist.id,
        "artist_name": show_artist.name,
        "artist_image_link": show_artist.image_link,
        "start_time": f'{show.start_time}'
    }
        )
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)

  show = Show(start_time=form.start_time.data)
  artist = Artist.query.get(form.artist_id.data)
  venue = Venue.query.get(form.venue_id.data)
  show.artist = artist
  show.venue = venue
  if (venue is None or artist is None):
    flash('Invalid Artist id or Venue id')
    return render_template('forms/new_show.html', form=form)

  # Check availability
  time = form.start_time.data.time()
  availabilities = [x.time for x in artist.availabilities]
  if availabilities and time not in availabilities:
    flash('Sorry! The artist will not be available on the selected time. Please choose another time.')
    return render_template('forms/new_show.html', form=form)

  try:
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('shows'))

@app.route('/availability/create')
def create_availability():
    form = AvailabilityForm()
    return render_template('forms/new_availability.html', form=form)

@app.route('/availability/create', methods=['POST'])
def create_availability_submission():
  form = AvailabilityForm(request.form)

  if form.validate():
    artist = Artist.query.get(form.artist_id.data)
    time = form.time.data
    new_availability = Availability(time=time)
    artist.availabilities.append(new_availability)

    try:
      db.session.commit()
      flash('New availability has been listed')
      return redirect(url_for('show_artist', artist_id=artist.id))
    except:
      db.session.rollback()
      flash('Failed to add new availability')
    finally:
      db.session.close()

  return render_template('forms/new_availability.html', form=form)

@app.route('/search_by_city')
def search_by_city():
  return render_template('pages/search_by_city.html')

@app.route('/search_by_city', methods=['POST'])
def search_by_city_submission():
  search_term = request.form.get('search_term')
  city = search_term.split(',')[0]
  state = search_term.split(',')[1].strip()

  venues = Venue.query.filter_by(state=state, city=city).all()
  artists = Artist.query.filter_by(state=state, city=city).all()

  data = {
    'count': len(venues) + len(artists),
    'venues': venues,
    'artists': artists
  }

  return render_template('pages/search_by_city.html', results=data, search_term=search_term)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')
#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='127.0.0.1', port=port)
