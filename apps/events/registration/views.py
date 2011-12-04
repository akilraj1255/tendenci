from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.template.defaultfilters import date as date_filter
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404, HttpResponse
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.views.decorators.csrf import csrf_exempt

from events.models import Event
from events.registration.constants import REG_CLOSED, REG_FULL, REG_OPEN
from events.registration.utils import get_available_pricings, reg_status
from events.registration.forms import PricingForm, RegistrantForm, RegistrationForm
from events.registration.formsets import RegistrantBaseFormSet

try:
    from notification import models as notification
except:
    notification = None

@csrf_exempt
def ajax_pricing_info(request, event_id, form_class=PricingForm, template_name="events/registration/pricing.html"):
    """
    Ajax query for pricing info.
    """
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == "POST":
        form = form_class(event, request.user, request.POST)
        if form.is_valid():
            pricing = form.cleaned_data['pricing']
            data = json.dumps({
                    "title":pricing.title,
                    "pk":pricing.pk,
                    "price":str(pricing.price),
                })
            return HttpResponse(data, mimetype="text/plain")
    else:
        form = form_class(event, request.user)
        
    return render_to_response(template_name,{
        'form':form,
    },context_instance=RequestContext(request))

def multi_register(request, event_id, template_name="events/registration/multi_register.html"):
    """
    This view is where a user defines the specifics of his/her registrations.
    A registration set is a set of registrants (one or many) that comply with a specific pricing.
    A pricing defines the maximum number of registrants in a registration set.
    A user can avail multiple registration sets.
    If the site setting anonymousmemberpricing is enabled,
    anonymous users can select non public pricings in their registration sets,
    provided that the first registrant of every registration set's email is validated to be an existing user.
    If the site setting anonymousmemberpricing is disabled,
    anonymous users will not be able to see non public prices.
    """
    event = get_object_or_404(Event, pk=event_id)
    
    # check if event allows registration
    if (not event.registration_configuration and event.registration_configuration.enabled):
        raise Http404
    
    # check if it is still open
    status = reg_status(event, request.user)
    if status == REG_FULL:
        messages.add_message(request, messages.ERROR, _('Registration is full.'))
        return redirect('event', event.pk)
    elif status == REG_CLOSED:
        messages.add_message(request, messages.ERROR, _('Registration is closed.'))
        return redirect('event', event.pk)
        
    # get available pricings
    pricings = get_available_pricings(event, request.user)
    
    # start the form set factory    
    RegistrantFormSet = formset_factory(
        RegistrantForm,
        formset=RegistrantBaseFormSet,
        can_delete=True,
        extra=0,
    )
    
    if request.method == "POST":
        # process the submitted forms
        reg_formset = RegistrantFormSet(request.POST,
                            prefix='registrant',
                            extra_params={
                                'pricings':pricings,
                            })
        reg_form = RegistrationForm(event, request.user, request.POST,
                            reg_count = len(registrant.forms))
        if reg_form.is_valid() and reg_formset.is_valid():
            print "VALIDATED"
    else:
        # intialize empty forms
        reg_formset = RegistrantFormSet(
                            prefix='registrant',
                            extra_params={
                                'pricings':pricings
                            })
        reg_form = RegistrationForm(event, request.user)
        
    return render_to_response(template_name, {
            'event':event,
            'reg_form':reg_form,
            'registrant': reg_formset,
            'pricings':pricings,
            }, context_instance=RequestContext(request))
