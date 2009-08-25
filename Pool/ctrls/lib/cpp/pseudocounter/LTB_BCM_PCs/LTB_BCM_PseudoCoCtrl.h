#ifndef LTB_BCM_PSEUDOCOCTRL_H_
#define LTB_BCM_PSEUDOCOCTRL_H_

#include <pool/PseudoCoCtrl.h>
#include <vector>

class LTB_BCM_PCs : public PseudoCounterController
{
 public:
  LTB_BCM_PCs(const char *,std::vector<Controller::Properties> &);
  virtual ~LTB_BCM_PCs();

  virtual double Calc(int32_t,std::vector<double> &);

 private:
  double e();
  double egap();
  double gap();
  double offset();
  double ibend();

  double read_device_attribute(std::string,std::string);

};

#endif /*LTB_BCM_PSEUDOCOCTRL_H_*/
