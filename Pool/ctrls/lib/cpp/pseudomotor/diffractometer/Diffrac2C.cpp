#include <string>
#include <sstream>

#include "Diffrac2C.h"

using namespace std;

//
//==============================================================================
//

const char *Diffrac2C_doc = 
	"This is the C++ pseudo motor controller for a Two circle diffractometer "
	"using the hkl library designed by SOLEIL";

const char *Diffrac2C_gender = "Diffractometer";
const char *Diffrac2C_model = "Two Circle";
const char *Diffrac2C_image = "2circle.png";
const char *Diffrac2C_organization = "CELLS - ALBA";
const char *Diffrac2C_logo = "ALBA_logo.png";

const char *Diffrac2C_pseudo_motor_roles[] = { "H", "K", "L", NULL };
const char *Diffrac2C_motor_roles[] = { "tth", "th", NULL };

long Diffrac2C_MaxDevice = 3; // should be the pseudo motor role #

Controller::PropInfo Diffrac2C_class_prop[] = {
		{"OperationMode", "Operation mode: 'Symetric' or 'Fix incidence'", "DevString", "Symetric"},
		{"a", "Lattice 'a' parameter", "DevDouble", "2.84"},
		{"b", "Lattice 'b' parameter", "DevDouble", "2.84"},
		{"c", "Lattice 'c' parameter", "DevDouble", "2.84"},
		{"alpha", "Lattice alpha angle", "DevDouble", "90"},
		{"beta", "Lattice beta angle", "DevDouble", "90"},
		{"gamma", "Lattice gamma angle", "DevDouble", "90"},
		{"wavelength", "the source wavelength", "DevDouble", "2.84"},
		{"direction", "the X-rays beam direction", "DevString", "1 0 0"},
		{"reflections", "list of reflections. Each reflection is a list of 6 numbers (space separated): th tth H K L lambda", "DevVarStringArray",""},
	{"DevName","The tango device name of the Diffractometer Device Server","DevString", "NONE"},
		{NULL} };

extern "C"
{
	
Controller *_create_Diffrac2C(const char *inst,vector<Controller::Properties> &prop)
{
	return new Diffrac2C(inst,prop);
}

}

Diffrac2C::Diffrac2C(const char *inst,vector<Controller::Properties> &prop):
Diffrac(inst,prop)
{ 
	init(inst,prop); 
}

Diffrac2C::~Diffrac2C ( ) 
{ }

hkl::twoC::vertical::Geometry &Diffrac2C::getGeometry()
{ 
	hkl::Geometry *g = diffractometer->geometry();
	if (!g)
	{
		Tango::Except::throw_exception("Diffrac2C_NoGeometry",\
										"Diffrac2C has no geometry.", 
										"Diffrac2C::getGeometry()");\
		
	}
	return *static_cast<hkl::twoC::vertical::Geometry*>(g); 
}

hkl::Diffractometer* Diffrac2C::createDiffractometer()
{
	return df_factory.create(hkl::DIFFRACTOMETER_TWOC_VERTICAL, 0.0);
}

/**
 * @brief
 * @param params 0 - reflection index
 *               1 - tth angle value
 *               2 - th angle value
 *               3 - h angle value
 *               4 - k angle value
 *               5 - l angle value
 * @return CMD_OK if successfull or error string otherwise
 */
const char *Diffrac2C::setReflection(vector<string> &params)
{
	if (params.size() < 6)
		return SET_REFLEC_WRONG_PARAMS;
	
	int i;
	double tth, th, h, k, l;
	if(!ToNumber(params[0], i) ||
	   !ToNumber(params[1], tth) ||
	   !ToNumber(params[2], th) ||
	   !ToNumber(params[3], h) ||
	   !ToNumber(params[4], k) ||
	   !ToNumber(params[5], l))
		return UNABLE_TO_PARSE_CMD_LINE;

	hkl::twoC::vertical::Geometry &g = getGeometry();
	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad; 
	g.set_angles(th, tth);
	
	hkl::Sample *sample = diffractometer->samples().current();
	hkl::ReflectionList &reflections = sample->reflections();
	if(reflections.size() <= i)
		reflections.add(hkl::svector(h,k,l));
	else
		reflections[i]->set_hkl(hkl::svector(h,k,l));
	return CMD_OK;
}

void Diffrac2C::setReflections(vector<string> &reflections)
{
	// add reflections
	if (reflections.size() > 0)
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		hkl::Sample &sample = getCurrentSampleRef();
		
		for(vector<string>::iterator it = reflections.begin();
			it != reflections.end(); ++it)
		{
			stringstream ss(*it);
			string buf;
			double tth,th,h,k,l;
			
			ss >> buf;
			bool res = ToNumber(buf, tth);
			ss >> buf;
			res &= ToNumber(buf, th);
			ss >> buf;
			res &= ToNumber(buf, h);
			ss >> buf;
			res &= ToNumber(buf, k);
			ss >> buf;
			res &= ToNumber(buf, l);
			
			if (res)
			{
				tth *= hkl::constant::math::degToRad;
				th *= hkl::constant::math::degToRad; 
				g.set_angles(th, tth);
				sample.reflections().add(hkl::svector(h, k, l));
			}
		}
	}
}

double Diffrac2C::CalcPhysical(int32_t axis,vector<double> &pseudo_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];
	double v;
	try
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		hkl::axe::Rotation *rot = (axis == 1) ? g.tth() : g.omega();
	
//		v = rot->get_current().get_value() * hkl::constant::math::radToDeg;

		v = rot->get_consign().get_value() * hkl::constant::math::radToDeg;

		cout << "[Diffrac2C] CalcPhysical("<< Diffrac2C_motor_roles[axis-1] 
			 << ", H=" << h << ", K=" << k << ", L=" << l << ") " << endl;		
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
	return v;
}

void Diffrac2C::CalcAllPhysical(std::vector<double> &pseudo_pos, 
                                std::vector<double> &physical_pos)
{
	double h = pseudo_pos[0];
	double k = pseudo_pos[1];
	double l = pseudo_pos[2];
	
 
	cout << "[Diffrac2C] Entering CalcAllPhysical(H=" << h << ", K=" << k 
		 << ", L=" << l << ")..." << endl;
	
	double tth, th, chi, phi;
	try
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		physical_pos[0] = tth = g.tth()->get_consign().get_value() * hkl::constant::math::radToDeg;
		physical_pos[1] = th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		
		cout << "[Diffrac2C] CalcAllPhysical(H=" << h << ", K=" << k << ", L=" << l 
			 << ") = (tth=" << tth <<", th=" << th << ", chi=" << chi << ", phi=" 
			 << phi << ") degrees" <<endl;		
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

/**
 * @brief Calculates H (axis 1) or K (axis 2) for the given tth and th angles. 
 * 
 * @param axis 1 for H and 2 for K
 * @param physical_pos array of tth,th motor position values
 * @return a value corresponding to the given axis for the given angles.
 */
double Diffrac2C::CalcPseudo(int32_t axis,vector<double> &physical_pos)
{
	double tth = physical_pos[0]; 
	double th = physical_pos[1]; // aka omega

	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;

	double h=0,k=0,l=0;
//	double &v = axis == 1 ? h : k ;
	double &v = axis == 1 ? h : (axis == 2 ? k : l) ;
	
	try
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		
		g.set_angles(th, tth);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		cout << "[Diffrac2C] CalcPseudo(axis="<< Diffrac2C_pseudo_motor_roles[axis-1] 
			 << ", tth=" << tth << ", th=" << th << ") = " 
			 << "(" << h << ", " << k << ", " << l << ")" << endl;		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
	return v; 
}

string Diffrac2C::calcA(vector<string> &params)
{
	if (params.size() != 3)
		return "Command calcA takes 3 arguments";
	
	double h, k, l;
	if(!ToNumber(params[0], h) ||
	   !ToNumber(params[1], k) ||
	   !ToNumber(params[2], l))
		return UNABLE_TO_PARSE_CMD_LINE;
	
	double tth, th;
	try
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		hkl::Mode *m = diffractometer->modes().get_current();

		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		m->computeAngles(h, k, l, UB);
		
		hkl::axe::Rotation *rot = NULL;
		tth = g.tth()->get_consign().get_value() * hkl::constant::math::radToDeg;
		th = g.omega()->get_consign().get_value() * hkl::constant::math::radToDeg;
		
		stringstream s;
		s << tth << " " << th;
		return s.str();
	}
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}

string Diffrac2C::calcHKL(vector<string> &params)
{
	if (params.size() != 2)
		return "Command calcHKL takes 2 arguments";
	
	double tth, th, chi, phi;
	if(!ToNumber(params[0], tth) ||
	   !ToNumber(params[1], th))
		return UNABLE_TO_PARSE_CMD_LINE;

	tth *= hkl::constant::math::degToRad;
	th *= hkl::constant::math::degToRad;
	
	double h=0,k=0,l=0;

	try
	{
		hkl::twoC::vertical::Geometry &g = getGeometry();
		
		g.set_angles(th, tth);
		
		hkl::smatrix UB = getCurrentSampleRef().get_UB();
		g.compute_HKL(h, k, l, UB);
		stringstream s;
		s << h << " " << k << " " << l << " ";
		return s.str();		
	}	
	catch(hkl::HKLException &e)
	{
		throw_TangoException(e);
	}
}
