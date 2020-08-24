#include <libsnark/common/default_types/r1cs_se_ppzksnark_pp.hpp>
#include <libsnark/zk_proof_systems/ppzksnark/r1cs_se_ppzksnark/r1cs_se_ppzksnark.hpp>
#include <libsnark/gadgetlib1/pb_variable.hpp>
#include <libsnark/gadgetlib1/gadgets/basic_gadgets.hpp>

#include "util.tcc"

using namespace libsnark;
using namespace std;

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
    typedef libff::Fr<default_r1cs_se_ppzksnark_pp> FieldT;

    // Initialize the curve parameters
    default_r1cs_se_ppzksnark_pp::init_public_params();

    r1cs_se_ppzksnark_verification_key<default_r1cs_se_ppzksnark_pp> vk;
    r1cs_se_ppzksnark_proof<default_r1cs_se_ppzksnark_pp> proof;
    r1cs_se_ppzksnark_primary_input<default_r1cs_se_ppzksnark_pp> primary_input;

    buffer_t vk_buf = readBuffer(argv[1]);
    buffer_t proof_buf = readBuffer(argv[2]);

    fromBuffer<r1cs_se_ppzksnark_verification_key<default_r1cs_se_ppzksnark_pp>>(&vk_buf, vk);
    fromBuffer<r1cs_se_ppzksnark_proof<default_r1cs_se_ppzksnark_pp>>(&proof_buf, proof);

 // verify
    bool verified = r1cs_se_ppzksnark_verifier_strong_IC<default_r1cs_se_ppzksnark_pp>(vk, primary_input, proof);

    cout << "Verification status: " << verified << endl;

    return 0;
}