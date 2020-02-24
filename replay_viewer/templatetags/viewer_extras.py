from django import template

from replay_viewer.utils import to_sprite

register = template.Library()

register.filter('to_sprite', to_sprite)
