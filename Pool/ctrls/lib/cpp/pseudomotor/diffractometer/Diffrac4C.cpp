#include <string>
#include <sstream>

#include "Diffrac4C.h"

using namespace std;

//
//==============================================================================
//

const char *Diffrac4C_doc = 
	"This is the C++ pseudo motor controller for a four circle vertical diffractometer "
	"using the hkl library designed by SOLEIL";

const char *Diffrac4C_gender = "Diffractometer";
const char *Diffrac4C_model  = "Four Circle";
const char *Diffrac4C_image  = "4circle.png";
const char *Diffrac4C_icon   = "Diffrac4C_icon.png";
const char *Diffrac4C_organization = "CELLS - ALBA";
const char *Diffrac4C_logo = "ALBA_logo.png";

const char *Diffrac4C_pseudo_motor_roles[] = { "H", "K", "L", NULL };
const char *Diffrac4C_motor_roles[] = { "tth", "th", "chi", "phi", NULL };

long Diffrac4C_MaxDevice = 3; // should be the pseudo motor role #

Controller::PropInfo Diffrac4C_class_prop[] = {
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
	{"reflections", "list of reflections. Each reflection is a list of 8 "
			        "numbers (space separated): tth th chi phi H K L lambda", 
			        "DevVarStringArray",""},
	{"DevName","The tango device name of the Diffractometer Device Server","DevString", "NONE"},
		{NULL} };

extern "C"
{
	
Controller *_create_Diffrac4C(const char *inst,vector<Controller::Properties> &prop)
{
	return new Diffrac4C(inst,prop);
}

}

Diffrac4C::Diffrac4C(const char *inst,vector<Controller::Properties> &prop):
Diffrac(inst,prop)
{ 
	init(inst,prop); 
}

Diffrac4C::~Diffrac4C ( ) 
{ }

hkl::eulerian4C::vertical::Geometry &Diffrac4C::getGeometry()
{ 
	hkl::Geometry *g = diffractometer->geometry();
	if (!g)
	{
		Tango::Except::throw_exception("Diffrac4C_NoGeometry",\
										"Diffrac4C has no geometry.", 
										"Diffrac4C::getGeometry()");\
		
	}
	return *static_cast<hkl::eulerian4C::vertical::Geometry*>(g); 
}

hkl::Diffractometer* Diffrac4C::createDiffractometer()
{
	hkl::Diffractometer *d = df_factory.create(hkl::DIFFRACTOMETER_EULERIAN4C_VERTICAL, 0.0);
	d->modes().set_current("Bissector");
	return d;
}

/**
 * @brief
 * @param params 0 - reflection index
 *               1 - tth angle value
 *               2 - th angle value
 *               3 - chi angle value
 *               4 - phi angle value
 *               5 - h angle value
 *               6 - k angle value
 *               7 - l angle value
 *               8 - lambda (optional - use current)
 * @return CMD_OK if successfull or error string otherwise
 */
const char *Diffrac4C::setReflection(vector<string> &params)
{
	if (params.size() < 8)
		return SET_REFLEC_WRONG_PARAMS;
	
	int i;
	double tth, th, chi, phi, h, k, l;
	if(!ToNumber(params[0], i) ||
	   !ToNumber(params[1], tth) ||
	   !ToNumber(params[2], th) ||
	   !ToNumber(params[3], chi) ||
	   !ToNumber(params[4], phi) ||
	   !ToNumber(params[5], h) ||
	   !ToNumber(params[6], k) ||
	   !ToNumber(params[7], l))
		return UNABLE_TO_PARSE_CMD_LINE;

	bool setLambda = 8 > params.size();
	double oldLambda = getGeometry().get_source().get_waveLength().get_value(); 
	if(setLambda)
	{
		double lambda;
		if (!ToNumber(params[8], lambda))
			return UNABLE_TO_PARSE_CMD_LINE;
		getGeometry().get_source().setWaveLength(lambda);
	}
	
	hkl::eulerian4C::vertical::Geometry &g = getGeometry();
	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	
	g.set_angles(th, chi, phi, tth);
	
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

void Diffrac4C::setReflections(vector<string> &reflections)
{
	// add reflections
	if (reflections.size() > 0)
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		hkl::Sample &sample = getCurrentSampleRef();
		
		for(vector<string>::iterator it = reflections.begin();
			it != reflections.end(); ++it)
		{
			stringstream ss(*it);
			string buf;
			double tth, th, chi, phi, h, k, l, lambda;
			
			ss >> buf;
			bool res = ToNumber(buf, tth);
			ss >> buf;
			res &= ToNumber(buf, th);
			ss >> buf;
			res &= ToNumber(buf, chi);
			ss >> buf;
			res &= ToNumber(buf, phi);
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
				tth *= hkl::constant::math::degToRad; 
				th *= hkl::constant::math::degToRad;
				chi *= hkl::constant::math::degToRad;
				phi *= hkl::constant::math::degToRad;
				g.set_angles(th, chi, phi, tth);
				sample.reflections().add(hkl::svector(h, k, l));
			}
		}
	}
}

double Diffrac4C::CalcPhysical(int32_t axis,vector<double> &pseudo_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];

cout << "[Diffrac4C] Entering CalcPhysical("<< Diffrac4C_motor_roles[axis-1] 
     << ", H=" << h << ", K=" << k << ", L=" << l << ")..." << endl;	
	double v;
	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		hkl::axe::Rotation *rot = NULL;
		if (axis==1) rot = g.tth();
		else if (axis==2) rot = g.omega();
		else if (axis==3) rot = g.chi();
		else if (axis==4) rot = g.phi();
	
		v = rot->get_current().get_value() * hkl::constant::math::radToDeg;

cout << "[Diffrac4C] CalcPhysical("<< Diffrac4C_motor_roles[axis-1] 
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
 * for the given tth, th, chi and phi angles. 
 * 
 * @param axis 1 for H, 2 for K and 3 for L
 * @param physical_pos array of tth,th,chi,phi motor position values
 * @return a value corresponding to the given axis for the given angles.
 */
double Diffrac4C::CalcPseudo(int32_t axis,vector<double> &physical_pos)
{
	double tth = physical_pos[0]; 
	double th  = physical_pos[1]; // aka omega
	double chi = physical_pos[2];
	double phi = physical_pos[3];

cout << "[Diffrac4C] Entering CalcPseudo(axis=" 
     << Diffrac4C_pseudo_motor_roles[axis-1] << ", tth=" << tth 
     << ", th=" << th << ", chi=" << chi << ", phi=" << phi << ") degrees..." << endl;	

	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;

	double h=0,k=0,l=0;
	double &v = axis == 1 ? h : (axis == 2 ? k : l) ;

	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		
		g.set_angles(th, chi, phi, tth);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
cout << "[Diffrac4C] CalcPseudo(axis="<< Diffrac4C_pseudo_motor_roles[axis-1] 
     << ", tth=" << tth << ", th=" << th << ", chi=" << chi << ", phi=" << phi 
     << ") rad = " << v << endl;		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
	
	return v; 
}

void Diffrac4C::CalcAllPhysical(std::vector<double> &pseudo_pos, 
                                std::vector<double> &physical_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];
	
cout << "[Diffrac4C] Entering CalcAllPhysical(H=" << h << ", K=" << k 
     << ", L=" << l << ")..." << endl;
    		 
	double tth, th, chi, phi;
	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		physical_pos[0] = tth = g.tth()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[1] = th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[2] = chi = g.chi()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		physical_pos[3] = phi = g.phi()->get_consign().get_value() * hkl::constant::math::radToDeg;
		
cout << "[Diffrac4C] CalcAllPhysical(H=" << h << ", K=" << k << ", L=" << l 
     << ") = (tth=" << tth <<", th=" << th << ", chi=" << chi << ", phi=" 
     << phi << ") degrees" <<endl;		
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

void Diffrac4C::CalcAllPseudo(std::vector<double> &physical_pos, 
                              std::vector<double> &pseudo_pos)
{
	double tth = physical_pos[0]; 
	double th  = physical_pos[1]; // aka omega
	double chi = physical_pos[2];
	double phi = physical_pos[3];

cout << "[Diffrac4C] Entering CalcAllPseudo(tth=" << tth << ", th=" << th 
     << ", chi=" << chi << ", phi=" << phi << ") degrees..." << endl;

	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;

	double h=0,k=0,l=0;
	
	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		
		g.set_angles(th, chi, phi, tth);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		
		pseudo_pos[0] = h;
		pseudo_pos[1] = k;
		pseudo_pos[2] = l;
		
cout << "[Diffrac4C] CalcAllPseudo(tth=" << tth << ", th=" << th << ", chi=" << chi << ", phi=" << phi 
     << ") rad = (h=" << h << ", k=" << k << ", l=" << l << ")" << endl;		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}	
}

string Diffrac4C::calcA(vector<string> &params)
{
	if (params.size() != 3)
		return "Command calcA takes 3 arguments";
	
	double h, k, l;
	if(!ToNumber(params[0], h) ||
	   !ToNumber(params[1], k) ||
	   !ToNumber(params[2], l))
		return UNABLE_TO_PARSE_CMD_LINE;

	double tth, th, chi, phi;
	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		tth = g.tth()->get_consign().get_value() * hkl::constant::math::radToDeg;
		th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		chi = g.chi()->get_consign().get_value() * hkl::constant::math::radToDeg;	
		phi = g.phi()->get_consign().get_value() * hkl::constant::math::radToDeg;
		
cout << "[Diffrac4C] CalcA(H=" << h << ", K=" << k << ", L=" << l 
     << ") = (tth=" << tth <<", th=" << th << ", chi=" << chi << ", phi=" 
     << phi << ") degrees" <<endl;		
		
		stringstream s;
		s << tth << " " << th << " " << chi << " " << phi;
		return s.str();
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

string Diffrac4C::calcHKL(vector<string> &params)
{
	if (params.size() != 4)
		return "Command calcHKL takes 4 arguments";
	
	double tth, th, chi, phi;
	if(!ToNumber(params[0], tth) ||
	   !ToNumber(params[1], th) ||
	   !ToNumber(params[2], chi) ||
	   !ToNumber(params[3], phi))
		return UNABLE_TO_PARSE_CMD_LINE;

	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	chi *= hkl::constant::math::degToRad;
	phi *= hkl::constant::math::degToRad;
	
	double h=0,k=0,l=0;

	try
	{
		hkl::eulerian4C::vertical::Geometry &g = getGeometry();
		
		g.set_angles(th, chi, phi, tth);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		
cout << "calcHKL(tth=" << tth << ", th=" << th << ", chi=" << chi << ", phi=" << phi 
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
