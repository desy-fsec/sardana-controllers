#include <string>
#include <sstream>

#include "Diffrac6C.h"

using namespace std;

//
//==============================================================================
//

const char *Diffrac6C_doc = 
	"This is the C++ pseudo motor controller for a six circle eulerian diffractometer "
	"using the hkl library designed by SOLEIL";

const char *Diffrac6C_gender = "Diffractometer";
const char *Diffrac6C_model  = "Six Circle";
const char *Diffrac6C_image  = "4circle.png";
const char *Diffrac6C_icon   = "Diffrac4C_icon.png";
const char *Diffrac6C_organization = "CELLS - ALBA";
const char *Diffrac6C_logo = "ALBA_logo.png";

const char *Diffrac6C_pseudo_motor_roles[] = { "H", "K", "L", NULL };
const char *Diffrac6C_motor_roles[] = { "mu", "th", "chi", "phi", "gamma", "delta", NULL };

long Diffrac6C_MaxDevice = 3; // should be the pseudo motor role #

Controller::PropInfo Diffrac6C_class_prop[] = {
	{"OperationMode", "Operation mode: 'Bissector', 'Delta Theta', "
			          "'Constant Omega', 'Constant Chi' or 'Constant Phi", 
			          "DevString", "Bissector"},
	{"a", "Lattice 'a' parameter", "DevDouble", "2.84"},
	{"b", "Lattice 'b' parameter", "DevDouble", "2.84"},
	{"c", "Lattice 'c' parameter", "DevDouble", "2.84"},
	{"alpha", "Lattice alpha angle", "DevDouble", "90"},
	{"beta", "Lattice beta angle", "DevDouble", "90"},
	{"gamma", "Lattice gamma angle", "DevDouble", "90"},
	{"wavelength", "the source wavelength", "DevDouble", "2.84"},
	{"direction", "the X-rays beam direction", "DevString", "1 0 0"},
	{"reflections", "list of reflections. Each reflection is a list of 10 "
			        "numbers (space separated): mu th chi phi gamma delta H K L lambda", 
			        "DevVarStringArray",""},
	{"DevName","The tango device name of the Diffractometer Device Server","DevString", "NONE"},
		{NULL} };

extern "C"
{
	
Controller *_create_Diffrac6C(const char *inst,vector<Controller::Properties> &prop)
{
	return new Diffrac6C(inst,prop);
}

}

Diffrac6C::Diffrac6C(const char *inst,vector<Controller::Properties> &prop):
Diffrac(inst,prop)
{ 
	init(inst,prop); 
}

Diffrac6C::~Diffrac6C ( ) 
{ }

hkl::eulerian6C::Geometry &Diffrac6C::getGeometry()
{ 
	hkl::Geometry *g = diffractometer->geometry();
	if (!g)
	{
		Tango::Except::throw_exception("Diffrac6C_NoGeometry",\
										"Diffrac6C has no geometry.", 
										"Diffrac6C::getGeometry()");\
		
	}
	return *static_cast<hkl::eulerian6C::Geometry*>(g); 
}

hkl::Diffractometer* Diffrac6C::createDiffractometer()
{
	hkl::Diffractometer *d = df_factory.create(hkl::DIFFRACTOMETER_EULERIAN6C, 0.0);
	d->modes().set_current("Bissector");
	return d;
}

/**
 * @brief
 * @param params 0  - reflection index
 *               1  - mu angle value
 *               2  - th angle value
 *               3  - chi angle value
 *               4  - phi angle value
 *               5  - gamma angle value
 *               6  - delta angle value
 *               7  - h angle value
 *               8  - k angle value
 *               9  - l angle value
 *               10 - lambda (optional - use current)
 * @return CMD_OK if successfull or error string otherwise
 */
const char *Diffrac6C::setReflection(vector<string> &params)
{
	if (params.size() < 10)
		return SET_REFLEC_WRONG_PARAMS;
	
	int i;
	double mu, th, chi, phi, gamma, delta, h, k, l;
	if(!ToNumber(params[0], i) ||
	   !ToNumber(params[1], mu) ||
	   !ToNumber(params[2], th) ||
	   !ToNumber(params[3], chi) ||
	   !ToNumber(params[4], phi) ||
	   !ToNumber(params[5], gamma) ||
	   !ToNumber(params[6], delta) ||
	   !ToNumber(params[7], h) ||
	   !ToNumber(params[8], k) ||
	   !ToNumber(params[9], l))
		return UNABLE_TO_PARSE_CMD_LINE;

	bool setLambda = 10 > params.size();
	double oldLambda = getGeometry().get_source().get_waveLength().get_value(); 
	if(setLambda)
	{
		double lambda;
		if (!ToNumber(params[10], lambda))
			return UNABLE_TO_PARSE_CMD_LINE;
		getGeometry().get_source().setWaveLength(lambda);
	}
	
	hkl::eulerian6C::Geometry &g = getGeometry();
	mu *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	gamma *= hkl::constant::math::degToRad;
	delta *= hkl::constant::math::degToRad;
	
	g.set_angles(mu, th, chi, phi, gamma, delta);
	
	hkl::Sample *sample = diffractometer->samples().current();
	hkl::ReflectionList &reflections = sample->reflections();
	if(reflections.size() <= i)
		reflections.add(hkl::svector(h,k,l));
	else
		reflections[i]->set_hkl(hkl::svector(h,k,l));
	
	if(setLambda)
		getGeometry().get_source().setWaveLength(oldLambda);
	
	return CMD_OK;
}

void Diffrac6C::setReflections(vector<string> &reflections)
{
	// add reflections
	if (reflections.size() > 0)
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		hkl::Sample &sample = getCurrentSampleRef();
		
		for(vector<string>::iterator it = reflections.begin();
			it != reflections.end(); ++it)
		{
			stringstream ss(*it);
			string buf;
			double mu, th, chi, phi, gamma, delta, h, k, l, lambda;
			
			ss >> buf;
			bool res = ToNumber(buf, mu);
			ss >> buf;
			res &= ToNumber(buf, th);
			ss >> buf;
			res &= ToNumber(buf, chi);
			ss >> buf;
			res &= ToNumber(buf, phi);
			ss >> buf;
			res &= ToNumber(buf, gamma);
			ss >> buf;
			res &= ToNumber(buf, delta);
			ss >> buf;
			res &= ToNumber(buf, h);
			ss >> buf;
			res &= ToNumber(buf, k);
			ss >> buf;
			res &= ToNumber(buf, l);
			ss >> buf;
			res &= ToNumber(buf, lambda);
			
			if (res)
			{
				getGeometry().get_source().setWaveLength(lambda);
				mu *= hkl::constant::math::degToRad; 
				th *= hkl::constant::math::degToRad;
				chi *= hkl::constant::math::degToRad;
				phi *= hkl::constant::math::degToRad;
				gamma *= hkl::constant::math::degToRad;
				delta *= hkl::constant::math::degToRad;
				g.set_angles(mu, th, chi, phi, gamma, delta);
				sample.reflections().add(hkl::svector(h, k, l));
			}
		}
	}
}

double Diffrac6C::CalcPhysical(int32_t axis,vector<double> &pseudo_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];

cout << "[Diffrac6C] Entering CalcPhysical("<< Diffrac6C_motor_roles[axis-1] 
     << ", H=" << h << ", K=" << k << ", L=" << l << ")..." << endl;	
	double v;
	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		hkl::axe::Rotation *rot = NULL;
		if (axis==1) rot = g.mu();
		else if (axis==2) rot = g.omega();
		else if (axis==3) rot = g.chi();
		else if (axis==4) rot = g.phi();
		else if (axis==5) rot = g.gamma();
		else if (axis==6) rot = g.delta();
	
		v = rot->get_current().get_value() * hkl::constant::math::radToDeg;

cout << "[Diffrac6C] CalcPhysical("<< Diffrac6C_motor_roles[axis-1] 
     << ", H=" << h << ", K=" << k << ", L=" << l << ") = " << v << endl;		
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
	return v;
}

/**
 * @brief Calculates H (axis 1) or K (axis 2) or L (axis 3) 
 * for the given mu, th, chi, phi, gamma and delta angles. 
 * 
 * @param axis 1 for H, 2 for K and 3 for L
 * @param physical_pos array of mu,th,chi,phi,gamma,delta motor position values
 * @return a value corresponding to the given axis for the given angles.
 */
double Diffrac6C::CalcPseudo(int32_t axis,vector<double> &physical_pos)
{
	double mu = physical_pos[0]; 
	double th  = physical_pos[1]; // aka omega
	double chi = physical_pos[2];
	double phi = physical_pos[3];
	double gamma = physical_pos[4];
	double delta = physical_pos[5];

cout << "[Diffrac6C] Entering CalcPseudo(axis=" 
     << Diffrac6C_pseudo_motor_roles[axis-1] << ", mu=" << mu 
     << ", th=" << th << ", chi=" << chi << ", phi=" << phi <<  ", gamma=" << gamma <<  ", delta=" << delta << ") degrees..." << endl;	

	mu *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	gamma *= hkl::constant::math::degToRad;
	delta *= hkl::constant::math::degToRad;

	double h=0,k=0,l=0;
	double &v = axis == 1 ? h : (axis == 2 ? k : l) ;

	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		
		g.set_angles(mu, th, chi, phi, gamma, delta);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
cout << "[Diffrac6C] CalcPseudo(axis="<< Diffrac6C_pseudo_motor_roles[axis-1] 
     << ", mu=" << mu << ", th=" << th << ", chi=" << chi << ", phi=" << phi << ", delta=" << delta << ", gamma=" << gamma << ") rad = " << v << endl;		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
	
	return v; 
}

void Diffrac6C::CalcAllPhysical(std::vector<double> &pseudo_pos, 
                                std::vector<double> &physical_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];
	
cout << "[Diffrac6C] Entering CalcAllPhysical(H=" << h << ", K=" << k 
     << ", L=" << l << ")..." << endl;
    		 
	double mu, th, chi, phi, gamma, delta;
	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		physical_pos[0] = mu = g.mu()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[1] = th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[2] = chi = g.chi()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		physical_pos[3] = phi = g.phi()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[4] = gamma = g.gamma()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		physical_pos[5] = delta = g.delta()->get_consign().get_value() * hkl::constant::math::radToDeg;
	

/*
		physical_pos[0] = mu = 0;
        physical_pos[1] = th = 45;
        physical_pos[2] = chi = 45;
        physical_pos[3] = phi = 90;
        physical_pos[4] = gamma = 0;
        physical_pos[5] = delta = 90;
*/	
cout << "[Diffrac6C] CalcAllPhysical(H=" << h << ", K=" << k << ", L=" << l 
     << ") = (mu=" << mu <<", th=" << th << ", chi=" << chi << ", phi=" 
     << phi << ", gamma=" << gamma << ", delta=" << delta << ") degrees" <<endl;		
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

void Diffrac6C::CalcAllPseudo(std::vector<double> &physical_pos, 
                              std::vector<double> &pseudo_pos)
{
	double mu = physical_pos[0]; 
	double th  = physical_pos[1]; // aka omega
	double chi = physical_pos[2];
	double phi = physical_pos[3];
	double gamma = physical_pos[4];
	double delta = physical_pos[5];

cout << "[Diffrac6C] Entering CalcAllPseudo(mu=" << mu << ", th=" << th 
     << ", chi=" << chi << ", phi=" << phi << ", gamma=" << gamma << ", delta=" << delta <<") degrees..." << endl;

	mu *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	gamma *= hkl::constant::math::degToRad;
	delta *= hkl::constant::math::degToRad;

	double h=0,k=0,l=0;
	
	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		
		g.set_angles(mu, th, chi, phi, gamma, delta);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		
		pseudo_pos[0] = h;
		pseudo_pos[1] = k;
		pseudo_pos[2] = l;
		
cout << "[Diffrac6C] CalcAllPseudo(mu=" << mu << ", th=" << th << ", chi=" << chi << ", phi=" << phi << ", gamma=" << gamma << ", delta=" << delta 
     << ") rad = (h=" << h << ", k=" << k << ", l=" << l << ")" << endl;		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}	
}

string Diffrac6C::calcA(vector<string> &params)
{
	if (params.size() != 3)
		return "Command calcA takes 3 arguments";
	
	double h, k, l;
	if(!ToNumber(params[0], h) ||
	   !ToNumber(params[1], k) ||
	   !ToNumber(params[2], l))
		return UNABLE_TO_PARSE_CMD_LINE;

	double mu, th, chi, phi, gamma, delta;
	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		mu = g.mu()->get_consign().get_value() * hkl::constant::math::radToDeg;
		th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		chi = g.chi()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		phi = g.phi()->get_consign().get_value() * hkl::constant::math::radToDeg;
		gamma = g.gamma()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		delta = g.delta()->get_consign().get_value() * hkl::constant::math::radToDeg;
		
cout << "[Diffrac6C] CalcA(H=" << h << ", K=" << k << ", L=" << l 
     << ") = (mu=" << mu <<", th=" << th << ", chi=" << chi << ", phi=" 
     << phi << ", gamma=" << gamma << ", delta=" << delta 
     << ") degrees" <<endl;		
		
		stringstream s;
		s << mu << " " << th << " " << chi << " " << phi << " " << gamma << " " << delta;
		return s.str();
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

string Diffrac6C::calcHKL(vector<string> &params)
{
	if (params.size() != 6)
		return "Command calcHKL takes 6 arguments";
	
	double mu, th, chi, phi, gamma, delta;
	if(!ToNumber(params[0], mu) ||
	   !ToNumber(params[1], th) ||
	   !ToNumber(params[2], chi) ||
	   !ToNumber(params[3], phi) ||
	   !ToNumber(params[4], gamma) ||
	   !ToNumber(params[5], delta))
		return UNABLE_TO_PARSE_CMD_LINE;

	mu *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	gamma *= hkl::constant::math::degToRad;
	delta *= hkl::constant::math::degToRad;
	
	double h=0,k=0,l=0;

	try
	{
		hkl::eulerian6C::Geometry &g = getGeometry();
		
		g.set_angles(mu, th, chi, phi, gamma, delta);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		
cout << "calcHKL(mu=" << mu << ", th=" << th << ", chi=" << chi << ", phi=" << phi << ", gamma=" << gamma << ", delta=" << delta 
     << ") rad = (h=" << h << ", k=" << k << ", l=" << l << ")" << endl;		
		
		stringstream s;
		s << h << " " << k << " " << l << " ";
		return s.str();		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}
