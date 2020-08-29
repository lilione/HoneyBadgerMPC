#include <libff/common/default_types/ec_pp.hpp>
#include <libsnark/gadgetlib1/gadgets/basic_gadgets.hpp>
#include <libsnark/gadgetlib1/gadgets/hashes/sha256/sha256_components.hpp>
#include <libsnark/zk_proof_systems/ppzksnark/r1cs_ppzksnark/r1cs_ppzksnark.hpp>

#include "random.hpp";
#include "sha256_value_comparison_gadget.hpp";
#include "util.tcc"

using namespace libff;
using namespace libsnark;
using namespace std;
using namespace unitn_crypto_fintech;

typedef libff::Fr<default_ec_pp> FieldT;

int main (int argc, char *argv[]) {
    default_ec_pp::init_public_params();

    protoboard<FieldT> pb;

    pb_variable<FieldT> value1;
    pb_variable<FieldT> value2;
    pb_variable_array<FieldT> commitment1;
    pb_variable_array<FieldT> commitment2;

    size_t commitment_size = div_ceil(SHA256_digest_size, FieldT::capacity());

    commitment1.allocate(pb, commitment_size, "commitment1");
    commitment2.allocate(pb, commitment_size, "commitment2");
    value1.allocate(pb, "value1");
    value2.allocate(pb, "value2");

    pb.set_input_sizes(2 * commitment_size);

    SHA256ValueGreaterEqGadget<FieldT> sha256_value_equal_gadget = SHA256ValueGreaterEqGadget<FieldT>(
    				pb,
    				value1,
    				value2,
    				commitment1,
    				commitment2,
    				"sha256_value_equal_gadget");
    sha256_value_equal_gadget.generate_r1cs_constraints();

    pb.val(value1) = atoi(argv[1]);
    pb.val(value2) = atoi(argv[2]);

    RandomBitVectorGenerator generator1 = RandomBitVectorGenerator{atoi(argv[3])};
	RandomBitVectorGenerator generator2 = RandomBitVectorGenerator{atoi(argv[4])};

	sha256_value_equal_gadget.generate_r1cs_witness(
    			generator1.generate_random_bit_vector(256),
    			generator2.generate_random_bit_vector(256));

    const r1cs_constraint_system<FieldT> constraint_system = pb.get_constraint_system();

    const r1cs_ppzksnark_keypair<default_ec_pp> keypair = r1cs_ppzksnark_generator<default_ec_pp>(constraint_system);

    auto commitments = pb.primary_input();

    const r1cs_ppzksnark_proof<default_ec_pp> proof = r1cs_ppzksnark_prover<default_ec_pp>(keypair.pk, commitments, pb.auxiliary_input());

    buffer_t vk_buf = createBuffer(keypair.vk);
    buffer_t proof_buf = createBuffer(proof);
    std::vector<buffer_t> buf_commitments;

    for (int i = 0; i < commitments.size(); i++) {
        buf_commitments.push_back(createBuffer(commitments[i]));
    }

    r1cs_ppzksnark_verification_key<default_ec_pp> new_vk;
    r1cs_ppzksnark_proof<default_ec_pp> new_proof;
    r1cs_ppzksnark_primary_input<default_ec_pp> new_commitments;

    fromBuffer<r1cs_ppzksnark_verification_key<default_ec_pp>>(&vk_buf, new_vk);
    fromBuffer<r1cs_ppzksnark_proof<default_ec_pp>>(&proof_buf, new_proof);

    for (int i = 0; i < buf_commitments.size(); i++) {
        FieldT commit;
        fromBuffer<FieldT>(&buf_commitments[i], commit);
        new_commitments.push_back(commit);
    }

    bool verified = r1cs_ppzksnark_verifier_strong_IC<default_ec_pp>(keypair.vk, commitments, proof);

    cout << "Verification status: " << verified << endl;

    verified = r1cs_ppzksnark_verifier_strong_IC<default_ec_pp>(new_vk, new_commitments, new_proof);

    cout << "Verification status: " << verified << endl;

    return 0;
}