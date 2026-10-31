import unittest


class RogTests(unittest.TestCase):
    def test_response_uses_battery_byte_six_and_separate_charge_query(self):
        from sources.rog import parse_battery, parse_charging
        packet = bytes([0xCC, 0x12, 0x07, 0, 0, 0, 73, 0, 1] + [0]*55)
        self.assertEqual(parse_battery(packet), 73)
        self.assertIsNone(parse_charging(packet))
        charge = bytes([0xCC, 0x12, 0x08, 0, 0, 1] + [0]*58)
        self.assertTrue(parse_charging(charge))

    def test_truncated_wrong_echo_nak_and_invalid_percentage_are_rejected(self):
        from sources.rog import parse_battery
        for packet in (b'', b'\xcc\x12\x07',
                       bytes([0xCC,0x12,8,0,0,0,80]),
                       bytes([0xCC,0xFF,0xAA,0,0,0,80]),
                       bytes([0xCC,0x12,7,0,0,0xFF,0xAA]),
                       bytes([0xCC,0x12,7,0,0,0,101])):
            self.assertIsNone(parse_battery(packet))
        self.assertEqual(parse_battery(bytes([0xCC,0x12,7,0,0,0,0])), 0)

    def test_only_verified_delta_interface_is_selected(self):
        from sources.rog import is_candidate
        self.assertTrue(is_candidate(dict(vendor_id=0x0B05, product_id=0x1AFA, interface_number=3, usage_page=0xFF00)))
        self.assertFalse(is_candidate(dict(vendor_id=0x0B05, product_id=0x1AD3, interface_number=3, usage_page=0xFF00)))
        self.assertFalse(is_candidate(dict(vendor_id=0x0B05, product_id=0x1AFA, interface_number=0, usage_page=1)))


if __name__ == '__main__':
    unittest.main()
