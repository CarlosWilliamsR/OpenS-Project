/**
 * Program IDL in camelCase format in order to be used in JS/TS.
 *
 * Note that this is only a type helper and is not the actual IDL. The original
 * IDL can be found at `target/idl/opens_anchor.json`.
 */
export type OpensAnchor = {
  "address": "8AcadEGS6Vmcj7kcQ8WroPoWioNkBhXFjkH8Db5hSVUX",
  "metadata": {
    "name": "opensAnchor",
    "version": "0.1.0",
    "spec": "0.1.0",
    "description": "Created with Anchor"
  },
  "instructions": [
    {
      "name": "registerRecord",
      "discriminator": [
        103,
        97,
        165,
        251,
        237,
        159,
        114,
        203
      ],
      "accounts": [
        {
          "name": "recordAccount",
          "writable": true,
          "pda": {
            "seeds": [
              {
                "kind": "const",
                "value": [
                  114,
                  101,
                  99,
                  111,
                  114,
                  100
                ]
              },
              {
                "kind": "arg",
                "path": "patientId"
              }
            ]
          }
        },
        {
          "name": "authority",
          "writable": true,
          "signer": true
        },
        {
          "name": "systemProgram",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "patientId",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "medicalHash",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "timestamp",
          "type": "i64"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "medicalRecord",
      "discriminator": [
        30,
        152,
        224,
        245,
        112,
        161,
        115,
        55
      ]
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "unauthorized",
      "msg": "Unauthorized authority to modify this record."
    },
    {
      "code": 6001,
      "name": "patientIdMismatch",
      "msg": "Patient ID does not match the PDA seed."
    }
  ],
  "types": [
    {
      "name": "medicalRecord",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "patientId",
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "medicalHash",
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "doctorPubkey",
            "type": "pubkey"
          },
          {
            "name": "timestamp",
            "type": "i64"
          }
        ]
      }
    }
  ]
};
