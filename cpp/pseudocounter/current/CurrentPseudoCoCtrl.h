#ifndef CURRENTPSEUDOCOCTRL_H_
#define CURRENTPSEUDOCOCTRL_H_

#include <pool/PseudoCoCtrl.h>
#include <vector>

class Current : public PseudoCounterController
{
public:
	Current(const char *,std::vector<Controller::Properties> &);
	virtual ~Current();

	virtual double Calc(int32_t, std::vector<double> &);
};

#endif /*CURRENTPSEUDOCOCTRL_H_*/
