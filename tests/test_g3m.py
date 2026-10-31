import unittest


class G3mTests(unittest.TestCase):
    def test_documented_battery_command_and_echoed_response_are_validated(self):
        from sources.g3m import battery_packet,parse_battery
        self.assertEqual(battery_packet(),bytes.fromhex('04 20 00 1A 06 00 00 00')+bytes(56))
        response=bytearray(bytes.fromhex('04 20 00 1A 06 00 00 00 5A 01 00 00 00 00')+bytes(50))
        self.assertEqual(parse_battery(response)['percent'],90)
        self.assertIsNone(parse_battery(response)['charging'])
        response[8]=0
        self.assertEqual(parse_battery(response)['percent'],0)
        response[8]=101
        self.assertIsNone(parse_battery(response))
        response[8]=70
        for index,value in ((0,3),(3,0xAA),(4,7),(7,0xFF),(7,0xFE)):
            invalid=bytearray(response)
            invalid[index]=value
            self.assertIsNone(parse_battery(invalid))
        self.assertIsNone(parse_battery(response[:9]))

    def test_actual_telink_g3m_vendor_collection_is_selected(self):
        from sources.g3m import is_candidate
        target=dict(vendor_id=0x320F,product_id=0x706E,manufacturer_string='Telink',
                    product_string='G3M PRO',interface_number=1,usage_page=0xFF1C,usage=0x92)
        self.assertTrue(is_candidate(target))
        self.assertFalse(is_candidate(target|dict(usage_page=1,usage=6)))
        self.assertFalse(is_candidate(target|dict(product_id=0x1234)))

    def test_descriptor_reports_define_probe_ids_and_lengths(self):
        from sources.g3m import feature_reports, probe_device
        # ID 2: 3 bytes; ID 7: 12 bits. Input/output declarations aren't probes.
        descriptor = bytes.fromhex('850275089503B102850775049503B1028509750895409102')
        self.assertEqual(feature_reports(descriptor), {2:4,7:3})
        class Device:
            def get_report_descriptor(self): return descriptor
            def get_feature_report(self, identifier, length):
                if (identifier,length) not in ((2,4),(7,3)):
                    raise AssertionError('Undeclared feature probe')
                return [identifier]+[50]*(length-1)
        sample = probe_device(Device())
        self.assertEqual(len(sample['reports']), 2)
        self.assertIsNone(sample['percent'])  # A byte in 0..100 is not proof of battery.

    def test_mchose_g3_is_never_selected_as_g3m(self):
        from sources.g3m import is_candidate
        self.assertFalse(is_candidate(dict(product_string='MCHOSE G3 V2',manufacturer_string='YJX-CHIP',usage_page=0xFF01)))
        self.assertTrue(is_candidate(dict(product_string='HECATE G3M PRO',manufacturer_string='EDIFIER',usage_page=0xFF00)))
        self.assertFalse(is_candidate(dict(product_string='HECATE G3M PRO',manufacturer_string='EDIFIER',usage_page=1)))


if __name__ == '__main__':
    unittest.main()
