#![no_std]

/// Vérifie si un octet correspond à un espace ASCII.
pub fn is_space(byte: u8) -> bool {
    byte == b' '
}

/// Encode un flux brut en un nombre de bits utiles selon le schéma :
/// espace = 1 bit ; autre octet = 9 bits (bit de contrôle + octet brut).
pub fn bit_count_for_bytes(data: &[u8]) -> usize {
    let mut total = 0usize;
    for &b in data {
        if is_space(b) {
            total += 1;
        } else {
            total += 9;
        }
    }
    total
}

/// Version minimale de codage sans allocation, en sortie dans un tampon fourni.
///
/// Cette implémentation est volontairement simple et compatible avec un moteur
/// bas niveau minimal, sans allocation dynamique sur le tas.
pub fn pack_space_aware(data: &[u8], output: &mut [u8]) -> Result<usize, ()> {
    let required = bit_count_for_bytes(data);
    let byte_count = (required + 7) / 8;

    if output.len() < byte_count {
        return Err(());
    }

    let mut bit_buffer: u64 = 0;
    let mut bit_count = 0usize;
    let mut out_index = 0usize;

    for &byte in data {
        if is_space(byte) {
            bit_buffer = (bit_buffer << 1) | 1;
            bit_count += 1;
        } else {
            bit_buffer = (bit_buffer << 9) | (u64::from(byte));
            bit_count += 9;
        }

        while bit_count >= 8 {
            bit_count -= 8;
            let extracted = ((bit_buffer >> bit_count) & 0xFF) as u8;
            output[out_index] = extracted;
            out_index += 1;
        }
    }

    if bit_count > 0 {
        let padded = ((bit_buffer << (8 - bit_count)) & 0xFF) as u8;
        output[out_index] = padded;
        out_index += 1;
    }

    Ok(out_index)
}

/// Décode un flux compacté avec le même schéma owl.
pub fn unpack_space_aware(data: &[u8], total_bits: usize) -> Result<Vec<u8>, ()> {
    let mut out = Vec::new();
    let mut bit_index = 0usize;

    while bit_index < total_bits {
        let byte_pos = bit_index >> 3;
        let bit_offset = 7 - (bit_index & 7);

        if byte_pos >= data.len() {
            return Err(());
        }

        let flag = (data[byte_pos] >> bit_offset) & 1;

        if flag == 1 {
            out.push(b' ');
            bit_index += 1;
        } else {
            if bit_index + 9 > total_bits {
                break;
            }
            let mut value = 0u8;
            for i in 0..8 {
                let pos = bit_index + 1 + i;
                let byte_pos2 = pos >> 3;
                let bit_offset2 = 7 - (pos & 7);

                if byte_pos2 >= data.len() {
                    return Err(());
                }

                value = (value << 1) | ((data[byte_pos2] >> bit_offset2) & 1);
            }
            out.push(value);
            bit_index += 9;
        }
    }

    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_spaces() {
        assert!(is_space(b' '));
        assert!(!is_space(b'A'));
    }

    #[test]
    fn compresses_basic_payload() {
        let data = b"A B";
        let required = bit_count_for_bytes(data);
        assert_eq!(required, 9 + 1 + 9);
    }
}
