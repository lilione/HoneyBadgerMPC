#include <libff/common/default_types/ec_pp.hpp>
#include <libsnark/zk_proof_systems/ppzksnark/r1cs_ppzksnark/r1cs_ppzksnark.hpp>

#include "util.tcc"

using namespace libff;
using namespace libsnark;
using namespace std;

typedef libff::Fr<default_ec_pp> FieldT;

int fromChar(char c) {
    if (c >= '0' && c <= '9') {
        return (c - '0');
    }
    else if (c >= 'A' && c <= 'F') {
        return (10 + (c - 'A'));
    }
    return (10 + (c - 'a'));
}

buffer_t readBuffer(const char* str) {
    int32_t len = strlen(str) / 2;

    buffer_t buffer;
    buffer.data = (uint8_t*)malloc(len);
    buffer.length = len;

    for (int32_t i = 0; i < len; ++i) {
        int v1 = fromChar(str[2 * i]);
        int v2 = fromChar(str[2 * i + 1]);
        buffer.data[i] = 16 * v1 + v2;
    }

    return buffer;
}

int main (int argc, char *argv[]) {
    default_ec_pp::init_public_params();

    buffer_t vk_buf = readBuffer(argv[1]);
    buffer_t proof_buf = readBuffer(argv[2]);

    std::vector<buffer_t> buf_commitments;
    for (int i = 3; i < 7; i++) {
        buf_commitments.push_back(readBuffer(argv[i]));
    }

    r1cs_ppzksnark_verification_key<default_ec_pp> vk;
    r1cs_ppzksnark_proof<default_ec_pp> proof;
    r1cs_ppzksnark_primary_input<default_ec_pp> commitments;

    fromBuffer<r1cs_ppzksnark_verification_key<default_ec_pp>>(&vk_buf, vk);
    fromBuffer<r1cs_ppzksnark_proof<default_ec_pp>>(&proof_buf, proof);

    for (int i = 0; i < buf_commitments.size(); i++) {
        FieldT commit;
        fromBuffer<FieldT>(&buf_commitments[i], commit);
        commitments.push_back(commit);
    }

    bool verified = r1cs_ppzksnark_verifier_strong_IC<default_ec_pp>(vk, commitments, proof);
    cout << "Verification status: " << verified << endl;

    return 0;
}