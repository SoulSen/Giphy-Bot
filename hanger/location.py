from hangups.hangouts_pb2 import Location as HangupsLocation, Place, EmbedItem

from hanger.abc import HangupsObject


class Location(HangupsObject):
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def _build_hangups_object(self):
        return HangupsLocation(
            place=Place(
                address=EmbedItem(
                    postal_address=EmbedItem.PostalAddress(
                        street_address=self.address
                    )
                )
            )
        )
