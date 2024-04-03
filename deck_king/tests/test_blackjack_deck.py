from ..blackjack.deck import *
from unittest import TestCase

# Test Card class, and its addition and values
ace = Card(Suit.HEARTS, 14)
two = Card(Suit.CLUBS, 2)
seven = Card(Suit.SPADES, 7)
ten = Card(Suit.DIAMONDS, 10)
queen = Card(Suit.DIAMONDS, 12)
king = Card(Suit.SPADES, 13)
jack = Card(Suit.HEARTS, 11)

class DeckTests(TestCase):
  def test_card_value(self):
    self.assertEqual(ace.card_value, CardValue([1, 11]))
    self.assertEqual(two.card_value, CardValue([2]))
    self.assertEqual(seven.card_value, CardValue([7]))
    self.assertEqual(ten.card_value, CardValue([10]))
    self.assertEqual(queen.card_value, CardValue([10]))
    self.assertEqual(king.card_value, CardValue([10]))
    self.assertEqual(jack.card_value, CardValue([10]))

  def test_card_addition(self):
    self.assertEqual(ace + two, CardValue([3, 13]))
    self.assertEqual(ace + seven, CardValue([8, 18]))
    self.assertEqual(ten + queen, CardValue([20]))
    self.assertEqual(queen + king, CardValue([20]))
    self.assertEqual(jack + ten, CardValue([20]))
    self.assertEqual(jack + seven, CardValue([17]))

    self.assertEqual(two + seven + ten, CardValue([2 + 7 + 10]))
    self.assertEqual(queen + jack + king, CardValue([10 + 10 + 10]))

    self.assertEqual(ace + two + seven, CardValue([1 + 2 + 7, 11 + 2 + 7]))
    self.assertEqual(ace + jack + ace + queen + seven + ten, CardValue([1 + 10 + 1 + 10 + 7 + 10,
                                                                       11 + 10 + 1 + 10 + 7 + 10,
                                                                       1 + 10 + 11 + 10 + 7 + 10,
                                                                       11 + 10 + 11 + 10 + 7 + 10]))

  def test_best_value(self):
    self.assertEqual((ace + two).best(), 13)
    self.assertEqual((ace + seven).best(), 18)
    self.assertEqual((ten + queen).best(), 20)
    self.assertEqual((queen + king).best(), 20)
    self.assertEqual((jack + ten).best(), 20)
    self.assertEqual((jack + seven).best(), 17)

    self.assertEqual((two + seven + ten).best(), 19)
    self.assertGreater((queen + jack + king).best(), 21)

    self.assertEqual((ace + two + seven).best(), 20)
    self.assertEqual((ace + two + ace + seven + ten).best(), 21)

  def test_deck(self):
    deck = Deck()
    self.assertEqual(len(deck.cards), 52)
    self.assertEqual(len(set(deck.cards)), 52)

    for _ in range(52):
      self.assertFalse(deck.is_empty())
      deck.draw()
    self.assertTrue(deck.is_empty())

  def test_deck_shuffle(self):
    deck = Deck()
    cards = deck.cards.copy()
    deck.shuffle()
    self.assertNotEqual(cards, deck.cards)
